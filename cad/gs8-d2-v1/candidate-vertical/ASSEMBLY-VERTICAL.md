# Vertical Pi candidate: assembly and service plan

**Shadow-gap ventilation candidate.** A plain integral cooler-side skin at Y−35.6 conceals separate cold and hot outer plenums; the original wall remains Y−28..−25.5 and the inner cavity datum stays fixed. Rear/underside mouths supply intake, and front/underside mouths discharge exhaust. The compact core is now 158 × 63.6 × 100 mm. The control panel is plain 2.8 mm: its four former grooves had 0.2 mm blind floors and were not through UPS vents. Compact uses 10 physical printed pieces represented by 9 CAD assembly rows; original storage adds the sleeve for 11 pieces / 10 rows. The tub body and bonded catch stub are separate prints. Gauge and coupons are excluded; no purchased-part substitution is authorized.

**PRINT HOLD.** The nominated source uses continuous windowed ribs on pillars, cold-mouth lintels and supported mouth mullions. Review its actual print poses, bridge directions and first layers. The three plenum coupons are geometry-only tests; no slicer, bridge, cleanout or physical-print release is established. The earlier post-grid and unsupported-mouth descriptions are historical.

**USB and CSI source corrections retained.** EVF power remains at source-registered USB2 and recording storage at USB3. The 12 × 27 mm R1 CSI tool opening remains straight and unsealed through the deeper side structure. It is a bypass around the intended cooling path; no seal, dust/water rating or airflow performance is implied. Actual cooler registration, latch/jaw operation, the full 200 mm FPC and complete EVF feed remain on HOLD.

**Unqualified review sequence, 2026-10-09. Not a fabrication or energization instruction.** No candidate has been
printed, assembled or physically tested. The scoped CAD evidence and its retained failures are listed below. All 56 inherited physical gates and
M1 remain open. This candidate sequence supersedes baseline step numbers only for the separate vertical design;
retain the electrical, optical, material and evidence rules in the baseline documents.

Frame: X toward the lens, Y toward the control panel/operator's left, Z up. Lens axis Y0/Z60. Pi/UPS/cooler form
one vertical module. The panel and carrier withdraw +Y. The USB recording stick withdraws −X. The microSD fits on the bench before carrier insertion and travels
with the stack; its withdrawal is permitted only with the panel removed (dog-leg: +X 18 mm, then +Y out of the open
side) and reach verified, or on the bench.

## Assembly STOP checkpoint

The current compact-Kowa export is a shadow-gap plenum candidate derived from reviewed export18. The earlier visible angled-channel trial is preserved in `vent-study/angled-channel-trial/` as a rejected visual alternative; its dimensions, throat values and 75 geometric passes do not validate the plenum. Its manifest and ventilation report live in `out/compact-kowa_lm6hc/`; the source geometry is `vent_geometry.py`. New evidence is valid only for the manifest hash recorded in that report. Re-export or source changes require rebinding, not reusing old pass counts.

The current manifest and its reports are listed in [REVIEW.md](REVIEW.md) and the [12 October corrective fix log](review-2026-10-10/FIX-LOG.md). Recheck the main audit, plenum geometry, path-aware flow, print and harness reports against that exact manifest. Preserve every failed row. The prior FX report contained the cooler/source-Pi conflict and bonded-catch tilt-window failures; the corrective geometry requires fresh evidence and does not qualify the printed joint. Cylinder and static-wire clearances cover declared geometric reserves only. Actual cooler, CSI latch, complete linked ribbon, EVF feed, J2 roots/stow and full flexible service remain HOLD.

The frozen export18 reference is preserved in `history/reviewed-export18/`, manifest
`c9e1e20710bb5f947ad47fa62328cebffb099fd3832d22909056bf8f1867cc76` (2026-10-09 07:46:39 UTC).
Its **288 pass / 2 fail / 18 info**, six scoped HDMI passes, 332 clear FPS material checks plus nine clear non-material diagnostics, two declared CSI cylinders, and 201 rigid power-service poses / 659 queries are historical evidence for that geometry. They are not automatically current passes for the revised tub or plenum. Alternative export18 reports remain historical. Fresh shadow-plenum Fujinon and original-storage exports, meshes, envelope and core-void comparisons now bind their own manifests; compact-Kowa service results do not transfer. See the [comparison and its limits](REVIEW.md#2-size-comparison-and-its-limits).

The frozen export18 raw failures are the active cooler/source-Pi overlap witness, **79.902671 mm³**, and the obsolete right-wall ray through the intentional CSI opening. The ray does not measure adjacent wall thickness. The frozen supplement's three adjacent 2.5 mm measurements describe the old wall. The new checker treats X−80/Z50 as an expected-empty CSI aperture test and separately probes the outer skin and original wall at X−110/Z50. Read its new manifest-bound result for the current count; the old 288/2/18 report remains preserved. Correcting this test context does not resolve the actual cooler/source conflict. Actual cooler profile and registration remain unresolved. Source Pi geometry retains 149 overlapping named-component solids; the raw sum is not occupied material, and the older 11.669 mm³ Boolean-difference witness is not an established lost-material volume.

The complete camera FPC and EVF feed remain unplaced. Storage plug clearance is a non-material reservation and does not establish actual mating. The intact 300 mm HDMI ribbon is retained; the fragile 200 mm study remains rejected. Both 270 mm power-path budgets include unresolved pad-root allowances, and the positive includes the 20 mm rigid fuse/joint zone. These are finished-path allocations, not copper-cut instructions. The 270 mm pigtail remains blocked by reach and hot-drop; a compatible proposal is pending with the 0.150 V limit unchanged. Complete flexible withdrawal, retained slack, hand/tool access and all physical tests remain STOPs. All 56 inherited gates and M1 remain open.

## 1. Safety and service prerequisite

Before opening the body or touching any internal connector:

1. Stop recording, let the take finish, request a clean shutdown and wait for the verified shutdown indication.
2. Remove external USB-C/bench power and any other possible power source.
3. Open the battery cap, pull the pack out using its ribbon, and physically part the XT30 junction by its housings.
   Keep exposed contacts protected. Confirm the pack is disconnected before touching internal leads.
4. Use the ESD mat/wrist strap for boards and flexes. Do not treat the J2 power button, a dark display or software
   shutdown as battery isolation. Never connect/disconnect internal leads with battery power attached.

Every service route below starts with all four prerequisites. Reassembly ends with the pack connected last,
only after enclosure closure and required checks. The pack is charged outside the body with the appropriate 1S
charger. Baseline BMS, polarity, fuse, power-feed and short-circuit requirements are unchanged.

## 2. Tools and hardware

The same straight PH1 system serves body screws, collar screws and specified stack screws. “One PH1” describes
screw drive compatibility, not the entire build. Retain the full baseline `ASSEMBLY.md` section 1.1 toolset and
bench/gate equipment, except its two hood-release pins: this candidate has no separate hood. In particular:

- Straight PH1 screwdriver and adjustable low-range torque PH1 driver, with the baseline tool-reach envelope
- Temperature-controlled soldering iron, solder/flux/wick and the correct M3 heat-set tip for that iron
- Stripper/cutter, heat gun, multimeter/thermocouple, fine tweezers and ESD equipment
- 1/2-inch deep socket for the CK1044 switch nut, used on the bushing axis (12.7 mm across-flats is the inherited
  reservation, not a published Lorlin dimension: confirm on receipt), saw/file, calipers/depth rod and soft-jaw vise
- Flat steel rule/bar, paint pens, fine smooth-jaw pliers, paper knob shims, panel prop/support and optional mirror
- Printed collar centring gauge, separately counted as a tool
- Current-limited bench supply, official Pi PSU, scope, logging USB power meter, electronic load and suitable charger
- Existing insert-repair tools and the camera tripod-block screw driver as a one-time bench exception

Provisionally allocate four existing-class 2.5 mm cable ties to separate red/black pigtail slack loops at the new carrier
lacing slots. Use them only if measured band thickness is ≤0.7 mm and head/tool clearance is proven. They must
not contact or press on the UPS PCB. This is an allocation from the baseline tie pack, not four extra packs.
Exact retention may change. Fixed tied folds cannot unfold for service; prove pack-disconnect reach with the
retention installed, without relying on opening a powered body first.

The new power-switch nut is run down with a deep socket on the button axis, never a spanner (straight-driver
rule, VN-46). Its across-flats is unmeasured: measure it on receipt and use an existing deep socket that fits, or
buy the matching one (BOM V-62). A review CAD probe found that a socket up to OD 28 mm clears the panel; actual
reach is unverified. This is a provisional tool, not a verified fit or a reason to omit the nut.
Preterminated J2 junction contacts are specified so routine build/service does not require a new crimp tool.

| Installed fasteners | Quantity and operation |
|---|---|
| PT 3.0 × 12 PH1 | 7: panel 4; carrier 2; independent grip lock 1 |
| Collar M3 × 10 PH1 | 3 with washers into the short tub inserts |
| Collar M3 × 16 PH1 | 1 with washer into the long pinch-lug insert |
| M3 inserts | 3 short, 1 long; not eight because spares were purchased |
| Stack M2.5 × 5 | 4 original upper screws |
| Stack M2.5 × 8 | 4 new lower screws replacing four original lower screws |
| Stack standoffs | 4 original supplied standoffs, actual length/thread depth measured |

Preserve baseline torque caps as provisional ceilings only: PT 0.35–0.5 N·m, collar anchors 0.15 N·m, collar pinch
0.2 N·m. No threadlocker on ASA and no casual re-torque. Revised coupons must establish usable values before
assembly. The original 0.2 N·m kit torque was metal-to-PCB; the new carrier also puts printed polymer under the
lower screws, so it is not automatically a qualified torque for this joint. Record PT drive counts and follow
the inherited limited-drive/repair policy. Do not use longer screws to force a bottomed-out standoff.

## 3. Qualification before the build sequence

- Read actual candidate checks, not the baseline pass summary. Resolve remaining interferences, ribbon widths,
  connector poses, slack storage and tool access before committing to prints.
- Complete the inherited measured-parts program, beginning with supported camera/lens setup and the EVF bench
  assembly. Match all real purchased-part identities, including X1203, cooler, pack, EVF and selected lens.
- Resolve new G-V-STACK, G-V-STORAGE, G-V-POWER, G-V-HDMI and G-V-PIGTAIL hold points in `REVIEW.md`.
- Run candidate slicer and coupon reviews for changed carrier, panel, tub, grip anchors and collar. Include the shadow plenums, bridges, posts and actual cleanout access; update load targets using the new mass. The old whole-tub structural binding and 0.90 N·m J4 coupon target do not qualify this revision. A baseline coupon result cannot qualify a changed joint automatically.
- Validate power, polarity and EVF feed on the bench under the inherited staged gates before any full build.
  Neither the stock diode feed nor the optional LDO is newly qualified by rotating the board.

## 4. Proposed build order

The numbered operations in each step are generated from [`steps.py`](steps.py), the candidate assembly-state model
(review FP-05), by [`make_assembly_text.py`](make_assembly_text.py). Do not edit them here: change `steps.py`, then
run `python make_assembly_text.py`; `--check` reports a stale or missing block. The paragraphs after each list are
hand-written details and holds; they never change the order.

Corrected order (12 October): bench optical work, prints and electrical preparation; seat the Pi end of the full
200 mm CSI cable before fitting the cooler, leaving the camera end free. Prepare grip, tub and strap, then lock the
grip. Fit collar and gauge on the empty tub lip; remove the gauge. Support the complete Pi module outside the body,
mate the camera end just before camera insertion, then fit and float the lens. Fit eyepiece and EVF, then the
linked module, EVF HDMI and power; inspect the already-mated CSI. Panel, four screws, FPS washer/nut/knob, media and
pack follow. The full 200 mm ribbon is omitted from the rigid camera and carrier sweeps, so this linked sequence
remains HOLD. Use the selected guide only when its receipt binds this source and the nominated manifest; earlier PDFs remain historical.

### B0. Supported optical setup (bench)

<!-- BEGIN:ops B0 -->
1. **`optics_bench`** Supported optical setup. Camera on its tripod block in a clamp, lens supported separately; never react lens thread torque through the PCB or cover. Seat the C-CS adapter, mark adapter/BFAR and BFAR/housing, measure infinity back focus, rear-cell clearance, cover reach and the lens support band; record actual values. Lens off again; tripod block and its 2 screws off and bagged. Keep the camera connector accessible. The official 200 mm FPC Pi end is seated before the cooler at module_bench; its camera end is mated while supported immediately before camera_in. Complete linked-ribbon motion remains HOLD.
   *Into the bench group:* `gs_camera`, `c_cs_adapter`. *Tools:* camera clamp/tripod block, lens support, tripod-block screw driver (one-time bench exception). *Review:* VN-44.

Bench step: nothing enters the body.
<!-- END:ops B0 -->

Details and holds: the CAD optical pose is not an infinity calibration. Keep the C-CS adapter correctly seated and the
witness marks across adapter/BFAR and BFAR/housing. Do not print or freeze a collar before these dimensions and the
revised M1/collar load requirements are settled. The Pi cable end is seated before the cooler at B2; the camera end remains free until the supported mating operation immediately before camera insertion in step 2. The linked full-length motion remains unproved.

### B1. Printed components and inserts (bench)

<!-- BEGIN:ops B1 -->
1. **`print_inserts`** After the print holds are closed: inspect the nominated parts and the selected lens's collar and centring gauge. Heat-set the 3 short tub inserts and the 1 long collar (pinch-lug) insert under the coupon-validated process, before any electronics are near. No insert may enter an optical, board or wiring clearance. Bond the printed +Y tab-catch stub into the tub (two-part epoxy V-68, default pending user decision 16): tenon into the pocket under the roof, stub pressed toward the camera axis (-Y) onto the pocket datum while it cures, no adhesive on the catch face (T2, VN-53).
   *Tools:* heat-set iron with the M3 tip; insert-repair tools.

Bench step: nothing enters the body.
<!-- END:ops B1 -->

Details and holds: after the print holds are closed, inspect and slice the nominated part set: compact has 10 physical prints / 9 CAD assembly rows; original storage adds the sleeve for 11 prints / 10 rows. Print the tub body and catch stub separately; do not omit the stub when counting material or process steps.
The horizontal optical and EVF bores require a declared support and slicer review; do not assume a support-free tub.
Base grip (C2, VN-57): paint supports only on the declared zone `grip_rear_pocket_passage_band` (`model.grip_support_zones`), the rear J4 head-pocket floor beside the power passage (x -82.75..-65.8, y -12.6..-3.8). The supports stand on the bed through the neck slot and window and never on the keyhole lips. Pull them out through the window, check that the pocket floor is flat, and slide the rear tongue through its full 10 mm by hand before the grip is used (the floor clears the tongue head by only 0.25 mm). The lens collar needs no support: the cone under the LR compression foot (C2, VN-58) carries it.
Inspect the separate cold/hot plenums, windowed beams, pillars, lintels and mouth mullions for sag, incomplete layer bonds and debris. Inspect all three coupon crops, including the all-four-mouths crop, before a production tub; open coupon edges cannot prove closed-body cleanout. The 6 mm gap is not a bridge span. Keep the outer skin on the declared bed face; verify actual toolpaths and do not enable inaccessible internal supports. The deeper CSI tunnel must remain straight and open. Remove accessible supports without damaging the skin/posts, optical datums, carrier ears or screw seats. Do not drill out the deleted panel grooves: the selected panel is plain 2.8 mm. Check the selected
lens's collar and separate centring gauge (a printed tool, never left in the body). Install the three short tub
inserts and one long collar insert under the coupon-validated process, on the bench before electronics are present.
Verify no insert enters an optical, board or wiring clearance. No hood, Pi keeper or printed power plunger is used.

### B2. Electrical and stack preparation, fully unpowered (bench)

<!-- BEGIN:ops B2 -->
1. **`module_bench`** Electrical and stack preparation, fully unpowered. Seat the Pi end of the official 200 mm camera FPC straight in CAM/DISP 1 with the correct contacts and latch, BEFORE fitting the Active Cooler, as the Raspberry Pi camera instructions recommend. Keep its camera end protected and free. Then stack Pi, X1203, cooler and the 4 standoffs on the carrier with the 4 M2.5 x 8 lower screws; OS microSD in. Solder the 16 AWG pigtail with its one inline fuse to the X1203 pads (RTV strain relief), the J2 signal half to the Pi J2 pads, the EVF feed and the leads. The CK1044 FPS switch belongs to THIS module: mate its inline pair here and carry the switch with the carrier, hand-supported; its washer, nut and knob are fitted only after the panel is on (op fps_washer_on..knob_fps_on). Pre-mate on the bench: the 3557 right-angle HDMI head on the Pi (300 mm 3562 ribbon pre-formed, EVF end free), the USB donor in the Pi USB2 port (EVF power, RCY pair half free), and the wall-facing GPIO housings (QT 1/3/5/6, 18/24 33/34) that cannot be reached once the carrier is in. Run pins 37/39 stay free for the run lead (op module_staged). Bench test only under the inherited gate, then disconnect all power again.
   *Into the bench group:* `carrier`, `pi5`, `cooler`, `x1203`, `x1203_kit`, `microsd`, `switch_1824`. *Mates:* `camera_fpc:pi`, `fps_1824:pi`, `fps_1824:sw`, `evf_hdmi:pi`, `evf_5v:pi`, `qt:pi`, `j2:pi`, `fan:pi`, `fan:cooler`, `xt30:pigtail`. *Tools:* soldering iron, multimeter, ESD strap, kit driver, PH1. *Review:* VN-40.

Bench step: nothing enters the body.
<!-- END:ops B2 -->

Details and holds (all on the bench, with the corrected CSI-before-cooler order):

1. Identify the actual Pi 5 J2 pads from the official drawing and board itself. Prepare the removable signal
   pair with one half soldered to the two J2 pads and the other to the two power-switch terminals. Insulate and
   strain-relieve all four joints. Confirm normally-open operation and continuity before power; never wire the
   switch into the battery current path. Use the keyed J2 set in the BOM (V-28): a 2-circuit wire-to-wire pair of a
   family used by no other junction in the camera (default Molex Micro-Fit 3.0 class, default pending user decision
   13; review VN-63), so no J2 half can mate the FPS PicoBlade pair or the EVF RCY pair. Socket (female) half on the
   J2 pads, pin (male) half on the switch; two distinct wire colours, labelled J2. Before soldering, run the try-mate
   matrix: each J2 half must refuse every other mateable half. Exact pad access, full connector placement, wire
   cuts/stow and mating access remain hold points (G-V-POWER). Pins, colours, lengths and plug order:
   [WIRING-VERTICAL.md](WIRING-VERTICAL.md).
2. Buy one 914.4 mm stock length of 16 AWG wire per colour. **Positive 270 mm is a finished-path allocation
   including a 20 mm rigid fuse/joint-sleeve zone.** Determine and trim actual copper cuts and solder overlaps
   to that finished path; do not cut 270 mm copper and then add a fuse. Both 270 mm total path budgets include unresolved
   pad-root allowances; they are not extra length to add later. No exact production cut or offcut is established. STOP until
   complete stored/extraction paths and joint allowances are proven. The current source model spans 0.14277 to
   0.16254 V at 8.6 A against the unchanged 0.150 V limit, including vendor-minimum copper and hot-fuse cases.
   The earlier nominal-only 0.142811 V margin is insufficient. Reach and hot-drop remain blocked; no wire, fuse,
   connector or cutoff substitution is adopted. See WIRING-VERTICAL section 8 for regenerated model values.
   Retain the pack's 60 mm 18 AWG lead and the near-XT30 positive inline fuse. Solder/insulate under the baseline
   fuse-temperature rules. Verify polarity and absence of shorts. Use the measured X1203 battery pads and
   neutral-cure RTV strain relief; do not move an assumed pad to make a route work.
3. Prepare the EVF feed (Adafruit 4448 red/black, 1N5817 in the + conductor with its band toward the EVF board,
   Pololu 2180 socket half on the USB side), the 18/24 lead and the QT lead exactly as the harness schedule in
   [WIRING-VERTICAL.md](WIRING-VERTICAL.md) states (both ends, colours, polarity, lengths). The baseline r7
   WIRING.md sections 5-7 are superseded for this fork. QT remains 250 ± 10 mm made from the two source leads;
   meter pin numbering instead of matching wire colours. Its four staggered splice joints need a new straight,
   accessible location in the vertical route. Do not import obsolete baseline absolute stow coordinates.
4. Bridge encoder A0 for address 0x37. Map the run, 18/24 and QT header leads before the stack becomes enclosed.
   Use the baseline pin mapping: QT physical pins 1/3/5/6, 18/24 pins 33/34, run pins 37/39. Do not substitute J2
   for a GPIO header pin or count the new button as a record control.
5. Seat the Pi end of the official 200 mm camera FPC straight in CAM/DISP 1 BEFORE fitting the Active Cooler,
   following the [official camera instructions](https://www.raspberrypi.com/documentation/accessories/camera.html).
   Confirm contact orientation and close the latch without a sharp bend. Keep the camera end protected and free.
   Then fit the Active Cooler once and keep its native fan lead with the stack. Assemble Pi, X1203 and the four actual
   standoffs at their original spacing. Retain four upper M2.5 × 5 screws. Replace the four lower M2.5 × 5 screws
   with four M2.5 × 8 through the carrier; bag the removed four. The head recess leaves 3 mm of carrier material,
   giving 3.4 mm nominal engagement beyond the 1.6 mm PCB. Measure thread depth and bottoming before tightening.
6. Test the stack only under the authorized inherited bench-gate procedure, then shut down/disconnect all power
   again. Fit the OS microSD on the bench before carrier insertion; it travels with the complete stack. Keep
   recording storage out for insertion. Routine service removes this whole
   assembled module; it does not repeatedly disturb cooler clips, thermal pads or pogo-pin geometry.
7. CK1044 FPS switch (conditional selection). Identify and retain the separate nut, mounting washer (receipt
   inclusion gate) and stop/tang washer. Set the stop for two adjacent 30° detents; continuity-test A and throw 2
   for open/high 18 and closed/low 24. Preserve that stop-ring setting during service. Measure and cut its shaft
   from the new panel's actual knob projection (dry fit in the panel only to measure, B3); do not reuse the old
   absolute Y cut value. The switch, with its inline pair mated, belongs to the module and is carried with the
   carrier, hand-supported; its mounting washer, nut and knob are bagged until step 6 (VN-40).

### B3. Control panel subassembly (bench)

<!-- BEGIN:ops B3 -->
1. **`panel_bench`** Panel subassembly, part 1. Paint-fill the engraving. Snap the encoder (A0 bridged, 0x37) into its cradle by pushing on the back of its board. Lay the 2 paper strips on the panel face round the encoder shaft, hold the panel with that thumb flat on the back of the encoder board and press knob_exp on until it stops on the paper (the thumb takes the push, not the hooks: r7 BX-5); pull the paper out. The FPS switch, its washer, nut and knob are NOT fitted here (they ride with the carrier, VN-40). If the CK1044 shaft must be cut, dry-fit the switch in this panel only to measure the knob projection, take it off and cut it off the panel.
   *Into the bench group:* `panel`, `encoder`, `knob_exp`. *Tools:* thumb backing, paper knob shims (2 strips), paint pen. *Review:* VN-40.
2. **`panel_power_switch`** Panel subassembly, part 2. Fit the Adafruit 1505 power button through the panel (flange on the outer face Y28) and run its nut down on the inner face (Y25.2) with a deep socket on the button axis, never a spanner; confirm thread length and socket reach on the real panel first. Keep the J2 junction half on its terminals free and accessible.
   *Into the bench group:* `power_button`, `power_nut_reserve`. *Drives:* `power_nut_reserve` (deep socket on the nut axis). *Tools:* deep socket on the nut axis (straight-driver rule; no spanner: VN-46). *Review:* VN-46.

Bench step: nothing enters the body.
<!-- END:ops B3 -->

Details and holds: mount the encoder in its cradle. Keep exposure and frame-rate markings minimal and legible. The
sole replacement power switch has “power” engraved above it; no indicator is added. Fit the Adafruit 1505 only
after confirming thread length, nut/washer and socket reach through the real panel. The panel is 2.8 mm thick, inner
Y25.2 and outer Y28. Its flange seats at Y28, centre X−20/Z25.5, and the power nut bears on Y25.2. Protect the back
terminals; do not use the unverified nut cylinder as a hardware specification. Keep its signal-junction half free
and accessible for later detachment. The panel carries no FPS hardware at this point: the CK1044 rides with the
module and its washer, nut and knob are fitted in step 6.

### B4. EVF subassembly (bench)

<!-- BEGIN:ops B4 -->
1. **`evf_bench`** EVF subassembly: foam pad stuck to the OLED back, native flex into the board ZIF and latch closed, as the qualified baseline optical module requires. No HDMI or power is mated to the board on the bench (both mate in the body at op evf_mate, after the carrier has brought their source ends).
   *Into the bench group:* `hmx039`, `foam_pad`, `evf_board`. *Tools:* tweezers, ESD strap.

Bench step: nothing enters the body.
<!-- END:ops B4 -->

Details and holds: prepare the EVF emitter, native flex and board as the qualified baseline optical module; adhesive
foam rides with the OLED. Keep contact orientation and ZIF latch operations as the real kit requires. The 3557
right-angle Pi head is pre-mated with the module (B2) and the 3556 straight EVF head mates in step 5; both only with
power absent and verified matching orientation. Both compact and original storage now conditionally use intact 300 mm 3562;
200 mm 3561 is a rejected study at quantity zero. Physical R3 bend capability, thickness, connector clocking and EMI remain gates. Support adapter bodies and provide
strain relief; do not pull on the ribbon or treat a friction connector as retained without a test.

### 1. Base/grip, tub and strap, then the grip lock

<!-- BEGIN:ops 1 -->
1. **`grip_prep`** Press the tripod nut into its grip pocket from the top. Feed the pre-wired run lead's 1-pin header housings up through the floor passage while it is open, then drop the run button into its cradle. The pack stays out (power last).
   *Enters:* `base_grip`, `tripod_nut`, `run_button`. *Mates:* `run_lead:grip`. *Tools:* flat bar for the tripod nut. *No rigid sweep:* press fits by hand (tripod nut slip fit, run button into its cradle); r7 swept neither.
2. **`strap_thread`** Thread the 12 mm strap through both upper and heel slots on the OPEN base, before the tub is seated: its pass over the bridge lies in the 2 mm recess in the base top, which the seated tub floor closes (r7 threads the strap before the tub too). It is then fitted BEFORE the grip lock: the p_grip driver handle passes about 1.37 mm from the strap, so the screw is driven (and audited) with the strap fitted.
   *Enters:* `strap`. *No rigid sweep:* flexible webbing threaded by hand; routing proxy only. *Review:* VN-23.
3. **`tub_on`** Seat the tub on the keyhole tongues in their keyed direction over the threaded strap, keeping the run lead in the passage; let its socket end hang out over the open +Y side. Do not lock yet.
   *Enters:* `tub`. *CAD motion:* `base_on`, not swept yet (open).
4. **`grip_lock`** Drive the independent grip-lock PT screw (p_grip) on its axis, 0.35-0.5 N m provisional, stop at head contact. The panel is never the grip lock.
   *Enters:* `p_grip`. *Drives:* `p_grip` (straight PH1 on the screw axis). *Tools:* straight PH1 driver on the screw axis (baseline bit/handle envelope); provisional torque cap per ASSEMBLY s2. *No rigid sweep:* screw: audited by the straight-driver check (FP-07) in this context, not swept.

In the body after this step: 6 ids (`steps.present_at`).
<!-- END:ops 1 -->

Details and holds: the lock is shifted 2 mm in Y, and upper strap anchors shift 12 mm in Y and 18.5 mm rearward in X.
Check the actual strap and lock clearances; the panel must not be the only thing preventing grip release. The strap
is threaded before the grip-lock screw because the p_grip driver handle passes close to it; the straight-driver
check (FP-07) audits p_grip with the strap fitted. The pack remains out.

### 2. Lens collar and gauge, camera, then lens (carrier and panel absent)

<!-- BEGIN:ops 2 -->
1. **`collar_on`** Lens collar FIRST, camera still out: bring the collar for the selected lens in along -X and set its feet on the tub front face over the 3 short inserts.
   *Enters:* `lens_collar`. *CAD motion:* `collar_on`, covered by the swept reverse `collar_off`. *Review:* VN-39.
2. **`collar_screws_start`** Start s_c1, s_c2, s_c3 (M3 x 10, washers) about 2 turns each from the front. Do not tighten.
   *Enters:* `s_c1`, `s_c2`, `s_c3`. *No rigid sweep:* screws started by hand; audited at collar_tighten.
3. **`gauge_in`** Push the centring gauge for this lens through the collar bore along -X until its rear cone seats in the empty tub lip and its front cone in the collar bore chamfer. The lip must be empty: the gauge and the camera/adapter can never be in the body together.
   *Enters:* `centring_gauge`. *CAD motion:* `gauge_in`, covered by the swept reverse `gauge_out`. *Review:* VN-39.
4. **`collar_tighten`** Hold the gauge home with a thumb and tighten s_c1, s_c2, s_c3 from the front to the provisional collar-anchor cap (0.15 N m), stopping at head contact.
   *Drives:* `s_c1`, `s_c2`, `s_c3` (straight PH1 on the screw axis). *Tools:* straight PH1 driver on the screw axis (baseline bit/handle envelope); provisional torque cap per ASSEMBLY s2; thumb holding the gauge home. *No rigid sweep:* screws tightened in place; audited with the gauge present.
5. **`gauge_out`** Pull the gauge out forward (+X) through the collar. The tub lip is now free for the camera.
   *Leaves:* `centring_gauge`. *CAD motion:* `gauge_out`, swept by verify_candidate.py. *Review:* VN-39.
6. **`camera_fpc_mate`** Support the camera and prepared Pi module beside the body, both unpowered. Seat the camera end of the full 200 mm FPC straight and close its latch before camera insertion. The Pi end was seated before the cooler at module_bench. Never let the ribbon carry either assembly; its full linked camera/module insertion and stored shape remain HOLD.
   *Mates:* `camera_fpc:cam`. *Tools:* ESD support for camera and complete Pi module. *No rigid sweep:* connector operation outside the body; actual latch and full linked FPC motion remain HOLD.
7. **`camera_in`** With all power absent and the prepared Pi module supported outside the body, mate the camera end of its 200 mm FPC at camera_fpc_mate before insertion; the Pi end was seated before the cooler at module_bench. HOLD until the full linked camera/module ribbon motion is checked. Bring camera with adapter in through the open +Y side: approach 11.1 mm rearward and 2 mm high, lower 2 mm, then move lensward (+X) 11.1 mm until the adapter passes the lip and the metal lock tab enters between the tab-catch tines. Keep the linked FPC slack and out of the path; do not let it carry either assembly. Do not leave it: nothing holds the camera back until the lens is on (next ops).
   *Enters:* `gs_camera`, `c_cs_adapter`. *CAD motion:* `camera_in`, swept by verify_candidate.py. **Flexible-motion HOLD:** HOLD: rigid camera/adapter sweep omits the complete 200 mm CSI FPC linking the camera to the supported module outside the body. Full-width stored material, linked motion, roots, bends and latch operation remain unproved; no complete assembly qualification. *Review:* VN-39, VN-44.
8. **`s_c4_start`** Fit the pinch screw s_c4 (M3 x 16, washer) loosely in the collar lug.
   *Enters:* `s_c4`. *No rigid sweep:* screw started loosely in the collar lug insert. *Review:* VN-41.
9. **`lens_in`** Lens with the carrier and panel still out (r7 step 8 method). Rest the body on its side so the open +Y side is up; one fingertip on the centre of the camera cover presses the camera forward (+X) onto its lip catch: push only, never pinch or turn the cover. Pass the lens through the collar and screw it into the adapter with fingertips until it stops, no extra snug; the camera turns with it until the metal lock tab meets the tab catch, which takes the torque through metal. Never react thread torque through the PCB or cover.
   *Enters:* `lens`. *Tools:* fingertips only; folded cloth for the side rest. *CAD motion:* `lens_in`, covered by the swept reverse `lens_out`. *Review:* VN-41.
10. **`lens_float`** Set iris and focus and push the lens gently rearward until it seats on the collar cone. With s_c4 still loose, turn lens and camera together the other way until the lock tab stops on the other tine, then back about half way: a soft stop each way means the tab floats between the tines. Look and feel: the camera now hangs on the lens and touches neither the tub lip, the counterbore nor the tines (J7-R float). Snug s_c4 on its axis to the provisional pinch cap (0.2 N m). Check both optical witness marks. The camera is now retained before anything else enters the body.
   *Drives:* `s_c4` (straight PH1 on the screw axis). *Tools:* straight PH1 driver on the screw axis (baseline bit/handle envelope); provisional torque cap per ASSEMBLY s2; hand on the grip until s_c4 is snug. *No rigid sweep:* rotation about the lens axis in place (roll window is FP-08 roll_catch), then a screw. *Review:* VN-41.

In the body after this step: 14 ids (`steps.present_at`).
<!-- END:ops 2 -->

Details and holds: the seated centring gauge overlaps the C-CS adapter by 927.75 mm³ in CAD and its rear cone
references the empty tub lip, so it is used only with the camera out (`steps.TOOLS`; lint TOOL_COEXIST). The nominal
CAD camera motion approaches with a small rearward and upward offset before seating forward on the lip; exact sampled
motion evidence and real finger/tool access still require qualification. **Do all of step 2 before the Pi carrier is
installed.** Do not claim that a camera can be forced past the vertical stack. Once the carrier is in, the camera can
retreat only 3.9 mm before it meets the carrier, so the fingertip push of the lens operation is possible only now
(VN-41). Between camera insertion and the snugged pinch screw nothing retains the camera: do not leave the body or
tip it nose-up in between. Use the integral roof's metal-tab torque catch, rather than the deleted hood catch, only
after its actual engagement is verified; the candidate roll window (r7 `roll_catch`) and the final-pose float check
(r7 `j7_float`) are computed checks not yet ported (FP-08), so the look-and-feel check does not replace them. Do not
leave a heavy lens cantilevered from an unsupported camera. Recheck infinity/back-focus and support after any collar
or adapter change; do not substitute visual centring for optical measurement.

### 3. Eyepiece and EVF module (no matings yet)

<!-- BEGIN:ops 3 -->
1. **`eyepiece_in`** From behind the body, push the eyepiece spigot +X through the rear-wall bore until its flange sits on the rear face; the spigot rests in the inner seat and the panel supplies the +Y clamp later (r7 step 6 method; the bore is closed above, so it cannot be dropped in from +Y). Keep the body level or nose-down until the panel is on.
   *Enters:* `eyepiece`. *CAD motion:* `eyepiece_in`, swept by verify_candidate.py.
2. **`evf_in`** Slide the OLED/board subassembly in from +Y into its seats, foam and native flex unstressed. Do NOT mate the EVF HDMI head or the EVF power junction yet: their source ends arrive with the carrier (op evf_mate). Do not let the unclamped module fall.
   *Enters:* `hmx039`, `foam_pad`, `evf_board`. *CAD motion:* `evf_in`, swept by verify_candidate.py. *Review:* VN-43.

In the body after this step: 18 ids (`steps.present_at`).
<!-- END:ops 3 -->

Details and holds: slide the qualified OLED/board assembly into its real seats from +Y, with foam/flex unstressed and
the eyepiece correctly supported. Do not bend the ribbon to compensate for a wrong head orientation later. Final panel
clamping happens in step 6; do not let the unclosed module fall. No EVF HDMI or EVF power is mated here (VN-43): the
3556 head and the USB donor's RCY half arrive with the module in step 4.

### 4. Insert the complete vertical carrier/stack

<!-- BEGIN:ops 4 -->
1. **`module_staged`** Hold the complete module (carrier, Pi, cooler, X1203, kit, OS microSD, FPS switch hand-supported, Pi HDMI head mated, EVF ends free) just outside the open +Y side. Plug the run lead from the grip onto Pi pins 37/39 (wall-facing: reachable only now). Carry the EVF HDMI head at least stroke + 3 mm below its mated height for the slide (VN-43 carried-head margin).
   *Mates:* `run_lead:pi`.
2. **`carrier_in`** Bring the module in along -Y onto its two bosses, feeding the pigtail and XT30 through the floor passage without scraping the pair, fuse or XT30 body. HOLD: the whole 200 mm camera FPC is linked at both ends and is absent from this rigid sweep. Prove its complete motion and keep it clear of the 3.9 mm camera-to-carrier gap during the slide. Recording storage stays out. Do not force the USB 5 V adapter aside.
   *Enters:* `carrier`, `pi5`, `cooler`, `x1203`, `x1203_kit`, `microsd`, `switch_1824`. *CAD motion:* `carrier_in`, covered by the swept reverse `carrier_out`. **Flexible-motion HOLD:** HOLD: rigid carrier sweep omits the complete 200 mm CSI FPC already connected to both camera and Pi. The full flexible sweep, stored slack, roots, bends and interaction with other looms are unproved; this operation is not a complete assembly or service pass. *Review:* VN-44.
3. **`carrier_screws`** Drive the two carrier PT screws (p_carrier1, p_carrier2) on their axes, 0.35-0.5 N m provisional, stop at head contact.
   *Enters:* `p_carrier1`, `p_carrier2`. *Drives:* `p_carrier1`, `p_carrier2` (straight PH1 on the screw axis). *Tools:* straight PH1 driver on the screw axis (baseline bit/handle envelope); provisional torque cap per ASSEMBLY s2. *No rigid sweep:* screws: audited by the straight-driver check (FP-07).

In the body after this step: 27 ids (`steps.present_at`).
<!-- END:ops 4 -->

Details and holds: the Pi HDMI head, the USB donor and the wall-facing GPIO housings were mated on the bench (B2).
Stage other Pi-end leads only under the verified insertion harness plan. Feed the camera pigtail only through the qualified source-driven swept passage, without scraping the
pair, single inline fuse or XT30 body. The local 3 mm corner relief retains 203.5/208 mm² nominal rear tongue
footprint; actual printed strength/wear remains gated. Use the current source/export rather than the obsolete
simple rectangular pocket dimensions. Outer grip, battery and cap dimensions remain unchanged.
The Z69 rear post and diagonal arm solve the modeled USB 5 V adapter collision. Confirm actual hardware
and full harness occupancy against the current export; do not force the adapter aside. Install the two carrier
PT screws only under the qualified assembly sequence. No cooler removal or pogo-interface redesign is part of this action.
The carried EVF HDMI head is held at least stroke + 3 mm below its mated height (VN-43). The existing carried sweep
lowers it only 6 mm, equal to its 6.0 mm stroke, so the stroke + 3 mm carry still needs its own sweep (check phase).

Keep the recording stick out: its −X removal axis and projecting housing must not be trapped during +Y carrier
movement. The bench-fitted microSD remains with the carrier. The camera, collar and lens were fitted and retained in
step 2; the camera cannot be fitted after this step.

### 5. Internal connections and slack

<!-- BEGIN:ops 5 -->
1. **`evf_mate`** Fully unpowered. Push the 3556 straight EVF HDMI head UP from below into the board receptacle by its body, never by the ribbon. Mate the EVF power RCY pair (2180 source half to 2181 EVF half) by both housings. The camera FPC is already mated at both ends: inspect its full width, roots and folds without releasing its latch; complete route and actual latch service remain HOLD. Seat and tug-test the header leads; route and secure the pigtail, run, 18/24 and EVF leads in their qualified lanes. Leave the QT and J2 leads FREE (out of their lanes): their panel ends mate at panel_prop, and a lead already secured cannot reach the propped panel (FP-10 mate_reach).
   *Mates:* `evf_hdmi:evf`, `evf_5v:evf`. *Tools:* tweezers, fingertip / steel-rule push stick, smooth-jaw pliers. *No rigid sweep:* no rigid part moves; connector and lead motions are harness checks (FP-10). *Review:* VN-43, VN-44.

In the body after this step: 27 ids (`steps.present_at`).
<!-- END:ops 5 -->

The Pi end was seated before the cooler at B2. With the module supported outside the body, the camera end was
mated immediately before camera insertion in step 2. Both ends were therefore linked during carrier insertion.
The current rigid camera/carrier sweeps omit the complete 200 mm FPC; `steps.flexible_scope()` and the main report
record that omission. STOP until the entire full-width stored ribbon and linked assembly/service motion, roots,
stiffeners, contact face and interaction with the other looms are proved. Real cable bend and flex-cycle limits
remain UNKNOWN; a round reservation is not a thin-ribbon material model.

The straight 12 × 27 mm R1 CSI opening remains unsealed and uncovered. Declared tool cylinders do not establish
actual latch/jaw access with the cooler retained. Do not repeat cooler removal to bypass this service HOLD. Here,
inspect the already-mated cable without releasing it, and mate the EVF HDMI head upward and the EVF power pair by
their bodies. The native fan lead and wall-facing header housings were mated on the bench. Verify physical pin
numbers and gently tug-test each seated socket.

Route and secure the 16 AWG pigtail, pack lead, run lead, QT, 18/24, J2 lead and EVF wiring in the lanes of the
harness schedule ([WIRING-VERTICAL.md](WIRING-VERTICAL.md)). These lanes are NOT yet qualified: the harness rows
listed there as failing (cable routes, cable stow, mate reach, lead access) are open, so this is a hold point.
The current XT30/junction pose is 21° yaw/45° pitch, with one inline fuse. The old side-mounted fuse has been
removed from the proxy; do not build two fuses by combining the old and new layouts. Fit and check the actual
junction against the source-driven pose; the rigid-motion pass is not proof that all flexible wire deploys or stows. Four carrier
through-slots, each 3 × 1 mm, are at (X,Z) = (−92,25), (−92,45), (−34,25), (−34,45) mm. Use the four measured
2.5 mm ties (band ≤0.7 mm) only under the qualified retention scheme for separate red/black cold-side loops.
Exact retention is still under review; a fixed tied fold must not be modeled as freely unfolding for service. Keep all tie bands/heads and
wire pressure off the UPS PCB. Do not tighten a tie into the insulation, reduce the qualified bend radius or
load the fuse terminals. Retain a straight supported fuse section; prove the whole installed wire length and
service reach before closure. Full stored-slack checks remain in progress.

Keep junctions, fuse sleeve and splices in accessible straight reservations. Avoid fan blades, optical parts,
carrier screw heads, vent paths and seam pinch lines. The HDMI ribbon needs a full-width, keyed-end route and
real bend/twist specification; a successful centreline drawing is not permission to pack it arbitrarily.
Use one intact 300 mm 3562 ribbon for either variant, with no virtual cut. The 200 mm 3561 study is rejected
and not installed. The refreshed full 300 mm exact study binds the selected shadow-plenum manifest; read its current report for the complete scoped check summary. The old
over-PCB tool failures remain rejected diagnostics; CSI operational access is still on HOLD. Complete interacting
loom service and actual FPC release remain STOPs. The developable 45° cylindrical fold does not qualify physical R3 bend, thickness,
clocking, EMI, service tolerance or retention.

The conditional EVF feed uses one Adafruit 4448 USB donor (catalog 300 mm; supplier drawing 325 ± 10 mm,
28 AWG, jacket Ø3.6 mm) and one each Pololu 2180/2181 Generic RCY-style pigtail (100 mm, 20 AWG).
Fit the 2180 socket-contact half on the USB source side and the 2181 pin-contact half on the EVF side.
The inline pair replaces the unsupported PH junction; it does not mate to a required EVF board socket.
Retain the diode and two traced EXT+/GND board joints. Two positive/diode joints plus one ground splice
preserve the existing three feed joints; no extra crimper is added. Final cuts/overlaps remain TBD.
Remove the four USB jumper ends; separately insulate the unused white and green data cores with two sleeves,
and add a shield sleeve only if present. Verify continuity/polarity, contact heating, retention and G-W6 drop.
The 32 × 7 × 7 mm junction reserve is provisional, with undimensioned male thickness and unmeasured mating;
USB overmold/exit geometry is also unknown. Neither a generic connector current rating nor fit is assumed.
Installed feed route (review H1, VN-60 / FP-11f; `routes.py` `usb_5v_feed`): GPIO-side USB2 port face, straight
through the head/bend allowance, down into the -Y channel behind the USB heads, forward along Z20.5 carrying the
splice zone (diode sleeve 30 × 4.8 × 4.8 mm with the option-C reserve 16 × 7.5 × 4.5 mm centred in it), up short
of the stored power loops, back along Z38.5 carrying the mated RCY pair (32 × 7 × 7 mm, X−146..−114), up the rear
corner and over the board rail onto the EVF 5 V pad point from above. The harness verifier checks the route and each
volume by exact Boolean against the closed camera and the HDMI ribbon cells, cable separation, and each Pololu tail
and the donor against its own stock with the r7 allowance (`feed_volumes`). The route holds only if the received USB
head ends within 24.7 mm of the port face; the option-C reserve is the default pending user decision 10 (VN-80);
RCY finger access at `evf_mate` and the 2181 half's parking during `carrier_in` are not modelled (HOLD).

For the FPS GPIO connection, use two measured female-ended stubs cut from an Adafruit 1950 pack,
not an unspecified Dupont-to-PH lead. The pack contains twenty 150 mm female/female 2.54 mm jumpers,
28 AWG; retain one female head on each of two coloured leads, leaving eighteen intact workshop spares.
Join the retained stubs to the selected PicoBlade male tails with two solder splices and two sleeves.
Final cuts, overlaps, head/insulation dimensions and the complete FPS route remain hold points; do not
install the full purchased wire length by assumption. No new crimper is required.

### 6. Close the control panel, then fit the FPS hardware

<!-- BEGIN:ops 6 -->
1. **`panel_prop`** Prop the panel subassembly beside the open side on a stable support, inner face toward the body, never hanging from wires. Mate the QT lead at the encoder and the J2 junction with both housings in reach.
   *Mates:* `qt:enc`, `j2:btn`.
2. **`panel_in`** Move the panel in along -Y, guiding the FPS switch bushing and its locating peg into the panel hole and slot while the other hand supports the switch body; lay the QT and J2 leads into their lanes as the panel closes. Confirm the camera catch and EVF clamp engage without pinching.
   *Enters:* `panel`, `encoder`, `knob_exp`, `power_button`, `power_nut_reserve`. *CAD motion:* `panel_in`, covered by the swept reverse `panel_out`. *Review:* VN-40.
3. **`panel_screws`** Drive the four panel PT screws on their axes, 0.35-0.5 N m provisional, stop at head contact. The FPS knob is not on yet, so the driver handle is clear of it.
   *Enters:* `p_panel1`, `p_panel2`, `p_panel3`, `p_panel4`. *Drives:* `p_panel1`, `p_panel2`, `p_panel3`, `p_panel4` (straight PH1 on the screw axis). *Tools:* straight PH1 driver on the screw axis (baseline bit/handle envelope); provisional torque cap per ASSEMBLY s2. *No rigid sweep:* screws: audited by the straight-driver check (FP-07) before the FPS knob is on.
4. **`fps_washer_on`** Fit the CK1044 mounting washer over the bushing on the panel face, stop/tang washer setting untouched.
   *Enters:* `fps_mounting_washer`. *CAD motion:* `fps_washer_on`, covered by the swept reverse `fps_washer_off`. *Review:* VN-40.
5. **`fps_nut_on`** Run the CK1044 nut down with a deep socket on the bushing axis and check anti-rotation (peg in slot).
   *Enters:* `fps_nut`. *Drives:* `fps_nut` (deep socket on the nut axis). *Tools:* deep socket on the nut axis (straight-driver rule; no spanner: VN-46). *CAD motion:* `fps_nut_on`, covered by the swept reverse `fps_nut_after_unthread`. *Review:* VN-40, VN-46.
6. **`knob_fps_on`** Lay the 2 paper strips round the FPS shaft and press knob_fps on, D flat to the shaft flat, until it stops on the paper (the nut on the panel takes the push); pull the paper out.
   *Enters:* `knob_fps`. *Tools:* paper knob shims (2 strips). *CAD motion:* `knob_fps_on`, covered by the swept reverse `fps_knob_off`. *Review:* VN-40.

In the body after this step: 39 ids (`steps.present_at`).
<!-- END:ops 6 -->

Details and holds: support the panel on a stable prop, not its wires. The 18/24 pair stays mated with the supported
switch/carrier assembly; it is disconnected only on the bench. Service reach/slack for the prop pose must be
measured; the baseline 60 mm prop offset is a starting target, not an inherited fit result. The corrected QT source
stores the complete nominal 250 mm lead and separately checks its 240–260 mm family in the existing envelope model.
The free propped-panel curve plus its fixed branch and 24 mm allowance is a minimum-reach budget, not the whole
stored cable. Do not add that allowance to the finished cable or treat remaining slack as automatically stowed.
Four 1.6 mm cores do not fit inside the round 3.2 mm bundle proxy: actual MP-QT packing, sleeves and roots remain
unqualified. The full flexible transition to panel closure is HOLD. J2 still requires actual pad, housing, root and
stow measurements. Read the current bound harness rows in WIRING-VERTICAL before using any route claim. Move the panel inward
along −Y without rotating it into the camera, EVF or stack. Confirm the tub bosses contact the panel pads at Y23.5
with no nominal seating gap; the face plate spans Y25.2..28. Tighten the four panel PT screws to the validated limit.
There is no hood to snap down and no hood-release pin operation. If slack cannot stow without force, stop and
re-route. The FPS mounting washer, nut and knob go on only after the panel screws; the nut is run down with a deep
socket on the bushing axis (straight-driver rule), and the socket's clearance to the panel face and the exposure
knob belongs to the straight-driver check (FP-07), not yet run for the candidate.

### 7. Recording media and eyecup

<!-- BEGIN:ops 7 -->
1. **`storage_in`** Remove and bag the drive cap (original storage: fit the sleeve on the bench first). Insert the one selected recording drive straight along +X into the upper USB3 port. Never two drives.
   *Enters:* `usb_stick`, `stick_sleeve`, `usb_storage_plug_reserve`. *CAD motion:* `storage_in`, covered by the swept reverse `storage_out`. *CAD motion:* `storage_plug_in`, covered by the swept reverse `storage_plug_reservation_through_enclosure`.
2. **`eyecup_on`** Push the eyecup over the eyepiece barrel from the rear.
   *Enters:* `eyecup`. *No rigid sweep:* TPU sleeve pushed over the eyepiece barrel (r7 swept none).

In the body after this step: 43 ids (`steps.present_at`).
<!-- END:ops 7 -->

The OS microSD was fitted on the bench before carrier insertion. **Do not insert or withdraw it with the
panel closed:** its +X path intersects the panel-mounted power-switch body. Insert the selected recording drive straight along +X into the upper USB3 port: compact Princeton PHD-USSD-500G or original
SDCZ880 with its own 185 mm body and sleeve. Remove and bag the Princeton cap first. Its published 34 × 15 × 7 mm
size includes that cap; the model conservatively reserves the full 34 mm outboard X−122..−156 plus an assumed
mating plug in the unchanged compact body. Verify real identity, fit, Linux/USB compatibility, bus power and
warm sustained ≥100 MB/s operation; vendor maximum speed is not a bench result. FIT Plus remains studied and
unadopted. Never install two drives or use the long SanDisk drive in the short enclosure.

The lens and its pinch screw were fitted in step 2, before the carrier. Any later lens or collar work follows the
lens or collar service route (section 5), never a lens fitted through the closed body without its turn-back.

### 8. Pack last and qualification

<!-- BEGIN:ops 8 -->
1. **`pack_in`** Only after closure and the bench checks: draw the pigtail XT30 out of the grip mouth, mate it to the pack XT30 by both housings outside the bay, push the junction and fuse in ahead of the pack, then the pack. Never mate inside the bay; never force the cap against the fuse or leads.
   *Enters:* `xt30_pair`, `pack`. *Mates:* `xt30:pack`. *CAD motion:* `pack_in`, not swept yet (open).
2. **`cap_on`** Slide the battery cap on until it latches.
   *Enters:* `cap`. *CAD motion:* `cap_on`, not swept yet (open).

In the body after this step: 46 ids (`steps.present_at`).
<!-- END:ops 8 -->

Details and holds: before reconnecting, inspect polarity, insulation, physical connector seating, free fan, clear vents, secure
strap/lock and unobstructed controls. Only after closure and required bench checks, mate the XT30 by its housings,
place the pack and slack/fuse safely in the grip, then close the cap. Never force the cap against the fuse or leads.

Run inherited closed-body electrical/workload/thermal/recording gates, including the unchanged 8.6 A and ≤0.15 V
pack-to-pads test, the fuse/contact temperatures, Pi rails and resets, warm ≥100 MB/s storage, EVF stability and
zero dropped frames. The swept floor passage adds body/grip air communication, and the unchanged CSI slot remains an unsealed bypass. Measure closed-body airflow/temperature with hand and strap in place, including rear/underside intake and front/underside exhaust mouth occlusion. Gross mouth or inner-slot area alone does not establish cooling. Record unobstructed, normal-hand, fitted-strap and stand/support positions as separate powered qualification cases. With the hot underside mouth blocked, only the nominated front-mouth neck remains. Use the current manifest and path-aware report, including rib/mullion obstruction; never credit a historical gross-mouth sum or infer rated operation with a blocked vent. Re-evaluate battery temperature, fan clearance and pressure loss. Re-run the revised collar, relieved tongue and strap
load/service tests. A J2 shutdown does not end the need
to disconnect the pack before reopening. Record measured results; no gate is closed by this written plan.

## 5. Service routes

All routes begin with section 1, including physical pack disconnection and removal of external power. The routes,
their removal order and the build operation that refits every removal are generated from `steps.py` `SERVICE`
(`steps.lint()` rule REFIT fails a removal without a refit). Refit with the whole-chain list given under each route
below and in the section 5.1 matrix: the build operations that put back this route AND every route done first, in
build order (section 1 last: pack and cap). Do not refit a route's own operations first and its prerequisites
afterwards: that order puts the carrier in before the lens (VN-41) and the pack in before the panel. `steps.lint()`
replays every documented refit from the end of its removal against the build rules (order, camera retention, tool
exclusion, fasteners, power last). A route's "do first" list is its complete dependency chain, not "where the
clearance requires it".

<!-- BEGIN:service-routes -->
**`safety`**: ASSEMBLY s1: shutdown, external power off, cap off, pack out, XT30 parted. Do first: nothing.

1. `svc_cap_off` Slide the battery cap off. *Refit:* `cap_on`.
2. `svc_pack_out` Pull the pack out by its ribbon and part the XT30 by its housings. (parts `xt30`) *Refit:* `pack_in`.

Refit, whole chain (this route and every route done first), in build order: `pack_in` -> `cap_on`.

**`panel`**: Control panel off (FPS hardware first, switch stays with the carrier). Do first: `safety`.

1. `svc_knob_fps_off` Pull knob_fps off along +Y. *Refit:* `knob_fps_on`.
2. `svc_fps_nut_off` Unthread the CK1044 nut with the deep socket, supporting the switch. (nut off `fps_nut` (deep socket)) *Refit:* `fps_nut_on`.
3. `svc_fps_washer_off` Take the mounting washer off; keep the stop/tang setting. *Refit:* `fps_washer_on`.
4. `svc_panel_screws_out` Remove the four panel PT screws. (screws out `p_panel1`, `p_panel2`, `p_panel3`, `p_panel4`) *Refit:* `panel_screws`.
5. `svc_panel_out` Translate the panel +Y over the released bushing and peg to the prop pose; part QT and J2 by their housings. (parts `qt`, `j2`) *Refit:* `panel_prop`, `panel_in`.

Refit, whole chain (this route and every route done first), in build order: `panel_prop` -> `panel_in` -> `panel_screws` -> `fps_washer_on` -> `fps_nut_on` -> `knob_fps_on` -> `pack_in` -> `cap_on`.

**`storage`**: Recording drive out along -X after safe removal. Do first: `safety`.

1. `svc_storage_out` Withdraw the drive straight along -X; do not rock the receptacle. *Refit:* `storage_in`.

Refit, whole chain (this route and every route done first), in build order: `storage_in` -> `pack_in` -> `cap_on`.

**`lens`**: Lens off in the closed body (same collar). s_c4 is only loosened. Do first: `safety`.

1. `svc_s_c4_loosen` Loosen s_c4 one turn on its axis. (loosened only `s_c4`) *Refit:* `lens_float`.
2. `svc_lens_out` Unscrew the lens with the tab catch taking the torque and draw it +X. *Refit:* `lens_in`.

Refit, whole chain (this route and every route done first), in build order: `lens_in` -> `lens_float` -> `pack_in` -> `cap_on`.

**`evf`**: EVF board/OLED out with the carrier in place. Do first: `safety` -> `panel`.

1. `svc_evf_unplug` Unplug the EVF HDMI head (down) and part the EVF power pair by both housings. (parts `evf_hdmi`, `evf_5v`) *Refit:* `evf_mate`.
2. `svc_evf_out` Release the panel clamp (panel is off) and slide the module +Y. *Refit:* `evf_in`.

Refit, whole chain (this route and every route done first), in build order: `evf_in` -> `evf_mate` -> `panel_prop` -> `panel_in` -> `panel_screws` -> `fps_washer_on` -> `fps_nut_on` -> `knob_fps_on` -> `pack_in` -> `cap_on`.

**`microsd`**: OS microSD; the closed-panel +X path is blocked by the power switch and the straight panel-off +X path by the lens collar. Do first: `safety` -> `panel`.

1. `svc_microsd_out` With the panel off, grip the card with straight fine-tip non-conductive tweezers, draw it +X 18 mm out of the socket, then lift it +Y out of the open panel side (dog-leg; the straight +X path meets the lens collar). Tool and finger reach are unqualified (HOLD, MEASUREMENTS-TO-CLOSE microSD row; VN-29). *Refit:* reverse of svc_microsd_out with the panel off once reach is qualified, or on the bench in module_bench with the module out (user decision VN-29).

Refit, whole chain (this route and every route done first), in build order: `panel_prop` -> `panel_in` -> `panel_screws` -> `fps_washer_on` -> `fps_nut_on` -> `knob_fps_on` -> `pack_in` -> `cap_on`.

**`module`**: Complete Pi/UPS/cooler module out (carrier with it). Do first: `safety` -> `storage` -> `panel`.

1. `svc_module_unplug` Unplug the EVF HDMI head at the EVF end and part the EVF power pair; release the camera FPC at the Pi (latch HOLD); free the pigtail in the grip passage (flexible: FP-10). (parts `evf_hdmi`, `evf_5v`, `camera_fpc`) *Refit:* `module_bench`, `evf_mate`; CSI Pi end only: use the connection named at module_bench with the assembled module supported; do not repeat cooler installation or soldering. HOLD until real latch access with the cooler retained and the complete linked-ribbon motion are proved.
2. `svc_carrier_screws_out` Remove the two carrier PT screws. (screws out `p_carrier1`, `p_carrier2`) *Refit:* `carrier_screws`.
3. `svc_carrier_out` Stage the module +Y with the FPS switch hand-supported; part the run lead at the staging pose. (parts `run_lead`) *Refit:* `module_staged`, `carrier_in`.
4. `svc_pigtail_out` The pigtail, fuse and its XT30 half leave with the module, drawn up through the floor passage (flexible withdrawal: FP-10 lead_access/pigtail checks). *Refit:* `pack_in`.

Refit, whole chain (this route and every route done first), in build order: `module_bench` -> `module_staged` -> `carrier_in` -> `carrier_screws` -> `evf_mate` -> `panel_prop` -> `panel_in` -> `panel_screws` -> `fps_washer_on` -> `fps_nut_on` -> `knob_fps_on` -> `storage_in` -> `pack_in` -> `cap_on`.

**`camera`**: Camera/adapter service and the first half of any lens change (VN-42 dependency chain). Do first: `safety` -> `panel` -> `storage` -> `module` -> `lens`.

1. `svc_camera_out` Reverse the camera-first insertion: -X 11.1, up 2, out +Y. *Refit:* `camera_in`.

Refit, whole chain (this route and every route done first), in build order: `module_bench` -> `camera_in` -> `lens_in` -> `lens_float` -> `module_staged` -> `carrier_in` -> `carrier_screws` -> `evf_mate` -> `panel_prop` -> `panel_in` -> `panel_screws` -> `fps_washer_on` -> `fps_nut_on` -> `knob_fps_on` -> `storage_in` -> `pack_in` -> `cap_on`.

**`collar`**: Collar swap for a different lens: camera out first (the gauge needs the empty lip), then the full refit from op collar_on. Do first: `safety` -> `panel` -> `storage` -> `module` -> `lens` -> `camera`.

1. `svc_collar_screws_out` Remove s_c1..s_c3 from the front. (screws out `s_c1`, `s_c2`, `s_c3`) *Refit:* `collar_screws_start`.
2. `svc_collar_off` Draw the collar +X off its feet; s_c4 stays in its lug insert. *Refit:* `collar_on`, `s_c4_start`.

Refit, whole chain (this route and every route done first), in build order: `module_bench` -> `collar_on` -> `collar_screws_start` -> `gauge_in` -> `collar_tighten` -> `gauge_out` -> `camera_in` -> `s_c4_start` -> `lens_in` -> `lens_float` -> `module_staged` -> `carrier_in` -> `carrier_screws` -> `evf_mate` -> `panel_prop` -> `panel_in` -> `panel_screws` -> `fps_washer_on` -> `fps_nut_on` -> `knob_fps_on` -> `storage_in` -> `pack_in` -> `cap_on`.

**`grip`**: Grip/base off. Default per VN-45: Pi module out first (the run lead's Pi end is reachable only with the carrier out); an inline junction is the user's alternative. Do first: `safety` -> `storage` -> `panel` -> `module`.

1. `svc_grip_screw_out` Remove the grip-lock PT screw from below. (screws out `p_grip`) *Refit:* `grip_lock`.
2. `svc_grip_off` Slide the grip off its keyholes with the run lead following through the floor passage; the strap stays threaded in the base and leaves with it. *Refit:* `grip_prep`, `strap_thread`; the strap stays threaded in the removed base (never re-thread it with the tub on: the seated tub floor closes its recess); slide base, tripod nut, run button and strap back together onto the keyholes (the base_on relative motion), then grip_lock.

Refit, whole chain (this route and every route done first), in build order: `module_bench` -> `grip_prep` -> `strap_thread` -> `grip_lock` -> `module_staged` -> `carrier_in` -> `carrier_screws` -> `evf_mate` -> `panel_prop` -> `panel_in` -> `panel_screws` -> `fps_washer_on` -> `fps_nut_on` -> `knob_fps_on` -> `storage_in` -> `pack_in` -> `cap_on`.
<!-- END:service-routes -->

### 5.1 r7 versus candidate service dependencies (VN-42)

Candidate columns are computed from `steps.py` (route closure, parts out, cables parted, refit chain); the r7 column
quotes the r7 release's ASSEMBLY section 7. Counts are state-model bookkeeping, not measurements.

<!-- BEGIN:service-matrix -->
| Target (route) | r7 baseline (r7 ASSEMBLY s7) | Candidate: routes first | Candidate: what comes out | Candidate refit (build ops, build order) | Change vs r7 |
|---|---|---|---|---|---|
| Isolation (section 1): `safety` | P1-P4: shutdown, cap off, pack out by its ribbon, XT30 parted by its housings. | none | 2 ids; 0 screws out; cables parted: xt30; J2 cycles: 0 | 2 ops: `pack_in`, `cap_on` | Same rule. |
| Control panel: `panel` | Items 3-5: eyecup off, 4 panel screws (hood-down pose), panel +Y about 60 mm, QT and 18/24 PH parted; the knobs ride with the panel. | `safety` | 14 ids; 4 screws out, 1 nut; cables parted: j2, qt, xt30; J2 cycles: 1 | 8 ops: `panel_prop`, `panel_in`, `panel_screws`, `fps_washer_on`, `fps_nut_on`, `knob_fps_on`, `pack_in`, `cap_on` | FPS knob, nut (deep socket) and washer come off first; the CK1044 switch stays with the module. Every panel removal is one cycle of the 30-cycle J2 pair (VN-42). |
| Recording drive: `storage` | Item 2: stick and sleeve out rearward (-X 70). | `safety` | 5 ids; 0 screws out; cables parted: xt30; J2 cycles: 0 | 3 ops: `storage_in`, `pack_in`, `cap_on` | Same direction. |
| Lens change, same collar (lens off and on): `lens` | "Lens swap": panel on, body closed, no isolation (nothing electrical is touched); s_c4 one turn, nose-down, fingertip unscrew; refit with the turn-back, s_c4 0.2 N m. | `safety` | 3 ids; 0 screws out, 1 loosened; cables parted: xt30; J2 cycles: 0 | 4 ops: `lens_in`, `lens_float`, `pack_in`, `cap_on` | Closed body as in r7, refit by the r7 nose-down method (5.2). The candidate keeps the isolation route first (conservative). |
| EVF board/OLED: `evf` | Item 7: pack out, panel off; HDMI unplugged downward, OLED/pad/board +Y 45, eyepiece -X 30. | `safety` -> `panel` | 17 ids; 4 screws out, 1 nut; cables parted: evf_5v, evf_hdmi, j2, qt, xt30; J2 cycles: 1 | 10 ops: `evf_in`, `evf_mate`, `panel_prop`, `panel_in`, `panel_screws`, `fps_washer_on`, `fps_nut_on`, `knob_fps_on`, `pack_in`, `cap_on` | Similar; the eyepiece stays. Finger/pliers corridor for the HDMI head not re-measured (VN-43). |
| OS microSD: `microsd` | Item 8: pack out; tweezers through the front slot, before the stack moves. | `safety` -> `panel` | 15 ids; 4 screws out, 1 nut; cables parted: j2, qt, xt30; J2 cycles: 1 | 8 ops: `panel_prop`, `panel_in`, `panel_screws`, `fps_washer_on`, `fps_nut_on`, `knob_fps_on`, `pack_in`, `cap_on`; plus the text refit of `svc_microsd_out` (section 5 routes) | Panel off first (closed-panel +X path blocked by the power switch); panel-off reach unqualified (VN-29, user decision). |
| Pi/UPS/cooler module: `module` | Item 10 (Pi stack): panel, lens, camera, collar, EVF, microSD and hood out first (items 3-9). | `safety` -> `storage` -> `panel` | 27 ids; 6 screws out, 1 nut; cables parted: camera_fpc, evf_5v, evf_hdmi, j2, qt, run_lead, xt30; J2 cycles: 1 | 14 ops: `module_bench`, `module_staged`, `carrier_in`, `carrier_screws`, `evf_mate`, `panel_prop`, `panel_in`, `panel_screws`, `fps_washer_on`, `fps_nut_on`, `knob_fps_on`, `storage_in`, `pack_in`, `cap_on`; plus the text refit of `svc_module_unplug` (section 5 routes) | Much shorter than r7: lens, camera, collar and EVF stay in. Passes through the module STOPs (FPC release, pigtail withdrawal, run-lead reach, fixed-to-carried leads). |
| Camera / adapter: `camera` | Items 6a-6b: pack out, panel off, lens off, camera -X 11.1 / up 2 / +Y 60; the collar may stay. | `safety` -> `panel` -> `storage` -> `module` -> `lens` | 30 ids; 6 screws out, 1 loosened, 1 nut; cables parted: camera_fpc, evf_5v, evf_hdmi, j2, qt, run_lead, xt30; J2 cycles: 1 | 17 ops: `module_bench`, `camera_in`, `lens_in`, `lens_float`, `module_staged`, `carrier_in`, `carrier_screws`, `evf_mate`, `panel_prop`, `panel_in`, `panel_screws`, `fps_washer_on`, `fps_nut_on`, `knob_fps_on`, `storage_in`, `pack_in`, `cap_on`; plus the text refit of `svc_module_unplug` (section 5 routes) | REGRESSION (VN-42): the whole module must come out first; the camera meets the carrier after 3.9 mm. User decision 5 (section 5.3). |
| Lens change, different collar (collar swap, e.g. Kowa to Fujinon): `collar` | Lens swap note + item 6c: panel off, lens and camera out (items 6a-6b), collar off, then step 7 with that collar's centring gauge (camera out), then step 8. | `safety` -> `panel` -> `storage` -> `module` -> `lens` -> `camera` | 35 ids; 9 screws out, 1 loosened, 1 nut; cables parted: camera_fpc, evf_5v, evf_hdmi, j2, qt, run_lead, xt30; J2 cycles: 1 | 23 ops: `module_bench`, `collar_on`, `collar_screws_start`, `gauge_in`, `collar_tighten`, `gauge_out`, `camera_in`, `s_c4_start`, `lens_in`, `lens_float`, `module_staged`, `carrier_in`, `carrier_screws`, `evf_mate`, `panel_prop`, `panel_in`, `panel_screws`, `fps_washer_on`, `fps_nut_on`, `knob_fps_on`, `storage_in`, `pack_in`, `cap_on`; plus the text refit of `svc_module_unplug` (section 5 routes) | REGRESSION (VN-42): full electronics teardown, because the gauge needs the empty lip and the camera needs the module out. User decision 5 (section 5.3). |
| Grip / base: `grip` | Item 11, after the Pi stack (items 8-10): run lead down through the floor hole, s_j out, base 10 mm rearward and off. | `safety` -> `storage` -> `panel` -> `module` | 32 ids; 7 screws out, 1 nut; cables parted: camera_fpc, evf_5v, evf_hdmi, j2, qt, run_lead, xt30; J2 cycles: 1 | 17 ops: `module_bench`, `grip_prep`, `strap_thread`, `grip_lock`, `module_staged`, `carrier_in`, `carrier_screws`, `evf_mate`, `panel_prop`, `panel_in`, `panel_screws`, `fps_washer_on`, `fps_nut_on`, `knob_fps_on`, `storage_in`, `pack_in`, `cap_on`; plus the text refit of `svc_module_unplug` (section 5 routes); plus the text refit of `svc_grip_off` (section 5 routes) | Same dependency: module out first (VN-45 default); an inline run-lead junction is user decision 11. |
<!-- END:service-matrix -->

### 5.2 Holds and methods for the routes

- **Control panel.** Support the switch while the FPS nut is unthreaded with the deep socket; preserve the stop/tang
  washer and its indexed setting. Translate the panel +Y over the released FPS shaft/bushing/peg only as far as
  verified clearance/slack permits, then part J2 and QT by their housings; no in-body FPS connector pull-out. Lift the
  detached panel away without hanging it from leads. Every panel removal is one mating cycle of the J2 pair
  (30-cycle tin contacts). STOP until this complete sequence is source-bound and physically qualified. Refit: panel,
  four screws, then washer, nut (deep socket) and knob (step 6).
- **Complete Pi/UPS/cooler module.** Recording storage out first; the bench-fitted microSD stays with the carried
  stack. Keep the Pi HDMI head and wall-facing GPIO housings mated. Release the camera FPC at the Pi only through
  qualified latch access. Free the already-isolated battery pigtail/fuse from the grip passage under the verified
  retention/release procedure; fixed tied loops cannot be assumed to unfold. STOP until actual FPC release, complete
  pigtail withdrawal, run-lead reach and every other fixed-to-carried lead have been proven. Stage the carrier +Y with
  headers, native fan lead, Pi-mated full HDMI, separately hand-supported FPS switch and complete still-mated FPS
  harness in their checked relative arrangement; part the run lead at the staging pose. The tub rest/guide stay fixed.
  Never hang the switch or module from wires. Cooler and standoffs stay assembled.
- **Lens change with the same collar (closed body).** r7 lens-swap method: loosen s_c4 one turn on its axis. Tip the
  isolated body nose-down, carry the lens with one hand and unscrew it with fingertips only; the tab catch takes the
  torque through metal. Check both witness marks; if the adapter came out with the lens, refit it before anything
  else (r7 rule; closed-body access for that is unverified in the candidate). Fit the lens the same way, carrying its weight; with the body nose-down the camera comes forward onto
  its lip catch before the thread starts. Push the lens rearward onto the collar cone. Body upright, one hand on the
  grip: with s_c4 still loose, turn lens and camera together the other way until the lock tab stops on the other tine,
  then back about half way, so the tab floats between the tines; snug s_c4 on its axis to the provisional 0.2 N m cap.
  The open-side look check of step 2 is not possible in the closed body: check by feel (soft stop each way).
- **Lens change needing a different collar.** This is the `collar` route: its full dependency chain and refit list
  are in section 5.1. Refit from `collar_on` with that lens's own collar and centring gauge (camera out, empty lip),
  then camera, lens with the turn-back, module, matings, panel, FPS hardware, storage and pack. The back focus was set
  for the B0 lens: check infinity with the new lens and, if it is off, reset it with the camera out (B0).
- **Camera / adapter.** The FPC Pi end is released in the module route; the camera end stays mated and leaves with
  the camera (unmate it on the bench, as B0). Reverse the camera-first insertion motion. Never pull the camera
  through the installed stack or react torque through its PCB. Refit camera, then lens and s_c4, before the carrier.
- **EVF.** Detach the panel; unplug EVF power by both junction housings and the HDMI head (downward) by its adapter
  body using verified tool access (finger/pliers corridor not re-measured, VN-43); protect the native flex, release the
  panel clamp and slide the module +Y. No ribbon pulling or forced fold.
- **Recording media.** With recording ended and safe removal completed, extract the drive straight −X through the rear
  recess; do not rock the Pi receptacle. The physical pack-disconnect prerequisite applies whenever this is part of
  internal service.
- **microSD.** Remove the control panel under its supported service procedure before any card withdrawal; the
  closed-panel path is blocked by the power-switch body and the straight panel-off +X path by the lens collar, so
  withdraw by the dog-leg (+X 18 mm, then +Y out of the open side; FP-12 `verify_microsd_service.py`). Confirm actual panel-off tool/hand reach, or carry the card
  with the complete stack and service it on the bench (VN-29, user decision). Preinstall the replacement card before
  carrier insertion. No cooler or PCB separation is required.
- **Grip/base (VN-45).** Default: Pi module out first, because the run lead's Pi end is a header housing on the
  wall-facing pins 37/39, reachable only with the carrier out (the button end is pre-wired). Then remove the grip-lock
  screw from below and slide the grip off its keyholes, the run lead following through the floor passage. Panel
  retention is not a substitute for that lock. Alternative, user decision 11: a removable inline run-lead junction near
  the grip mouth would let the grip come off without the module route; it is not adopted and no part is selected.

### 5.3 User decision 5 (VN-42): carrier-out camera service, not decided here

The routes above model option A, which is what the current geometry allows. The choice belongs to the user:

- **Option A, accept the trade.** Camera, collar and any lens change that needs a different collar go through the full
  module route (section 5.1): one J2 cycle per opening, the module STOPs, and a collar change always removes the
  camera because the centring gauge needs the empty lip. r7 needed only the pack out and the panel off for camera
  service.
- **Option B, redesign.** (B1) Let the camera leave ahead of the carrier front (review VN-42: X−29), so camera service
  needs only the panel, as in r7; or (B2) a centring gauge that seats without entering the lip, so a collar can be
  re-centred with the camera in place (camera service still needs the module route unless B1 is also done). Either
  redesign changes `steps.SERVICE` (`camera` / `collar` requires) and needs new motion rows; neither is modelled.

Reassemble in reverse dependency order: collar and centring gauge (camera out) before the camera, lens and pinch screw
before the carrier, EVF and FPC matings before the panel, FPS washer, nut and knob after the panel screws, pack
last. Recheck witness marks and the final collar pinch after lens work. Repeated-cycle qualification includes
real fingers/tools, actual leads/connectors and the fitted strap; sampled CAD sweeps alone are insufficient. Nominal-feature constants are report-only analytical values, not
measured-feature pass results. The frozen export18 rigid report retains its two raw failures; scoped CAD passes do not
qualify physical assembly or the complete interacting loom.

## 6. Records and completion criteria

For each changed part/joint record the exact source/export identity, measured parts, print/material settings,
coupon results, service-cycle results and any failed or changed dimensions. Keep adverse results visible. Do not
inherit a baseline “pass” from a different orientation, cable or collar. Use `REVIEW.md` for candidate hold points
and the existing evidence format for the inherited physical gates. No final build/recording claim is made here.

References: [concealed-vent structural supplement](structural-review/CONCEALED-VENT-STRUCTURAL.md), [candidate BOM](BOM-VERTICAL.md), [candidate review](REVIEW.md), [baseline assembly](../ASSEMBLY.md),
[candidate wiring](WIRING-VERTICAL.md) (supersedes baseline wiring sections 2 and 5-7 for this fork), [baseline wiring](../../../electronics/gs8-d2-v1/WIRING.md) (sections 4, 8 and 9 still apply), [baseline handoff](../HANDOFF.md).
