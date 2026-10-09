# Vertical Pi candidate: assembly and service plan

**Shadow-gap ventilation candidate.** A plain integral cooler-side skin at Y−35.6 conceals separate cold and hot outer plenums; the original wall remains Y−28..−25.5 and the inner cavity datum stays fixed. Rear/underside mouths supply intake, and front/underside mouths discharge exhaust. The compact core is now 158 × 63.6 × 100 mm. The control panel is plain 2.8 mm: its four former grooves had 0.2 mm blind floors and were not through UPS vents. Nine compact production parts and all purchased selections/quantities are retained.

**PRINT HOLD.** The front mouth removes the frame beneath the first roof layer over Z5..40. A nominal 10.7 mm distance there is not a two-ended supported bridge; raster direction may require about 35 mm of bridging. The expanded coupon contains this region. Freeze geometry for review, but do not release the tub for printing until slicer paths, bridge behavior and cleanout are demonstrated.

**USB and CSI source corrections retained.** EVF power remains at source-registered USB2 and recording storage at USB3. The 12 × 27 mm R1 CSI tool opening remains straight and unsealed through the deeper side structure. It is a bypass around the intended cooling path; no seal, dust/water rating or airflow performance is implied. Actual cooler registration, latch/jaw operation, the full 200 mm FPC and complete EVF feed remain on HOLD.

**Unqualified review sequence, 2026-10-09. Not a fabrication or energization instruction.** No candidate has been
printed, assembled or physically tested. The scoped CAD evidence and its retained failures are listed below. All 56 inherited physical gates and
M1 remain open. This candidate sequence supersedes baseline step numbers only for the separate vertical design;
retain the electrical, optical, material and evidence rules in the baseline documents.

Frame: X toward the lens, Y toward the control panel/operator's left, Z up. Lens axis Y0/Z60. Pi/UPS/cooler form
one vertical module. The panel and carrier withdraw +Y. The USB recording stick withdraws −X. The microSD fits on the bench before carrier insertion and travels
with the stack; its +X withdrawal is permitted only with the panel removed and reach verified, or on the bench.

## Assembly STOP checkpoint

The current compact-Kowa export is a shadow-gap plenum candidate derived from reviewed export18. The earlier visible angled-channel trial is preserved in `vent-study/angled-channel-trial/` as a rejected visual alternative; its dimensions, throat values and 75 geometric passes do not validate the plenum. Its manifest and ventilation report live in `out/compact-kowa_lm6hc/`; the source geometry is `vent_geometry.py`. New evidence is valid only for the manifest hash recorded in that report. Re-export or source changes require rebinding, not reusing old pass counts.

Current selected manifest `53e668d43847acd1f59d2b559a562476c54a23db0918debd482d632f0e8ceb77` has **292 pass / 1 fail / 18 info** in the main audit. The failure is the retained **79.902671 mm³** cooler/source-Pi conflict. The separate plenum report has **49 pass / 0 fail / 21 info**; current HDMI has six scoped passes, FPS has 332 clear material checks plus nine clear non-material diagnostics, and rigid power service has 201 poses / 659 exact queries with no hits. The declared CSI cylinders and static power-wire checks pass their narrow geometric scope; actual CSI operation stays on HOLD. The new dedicated USB-head report passes the bounded installed-head reservation against the complete current tub and accepted support-source hashes. The earlier missing-extract attempt remains historical. Received overmold/exit, full EVF feed and actual service still remain unqualified.

The frozen export18 reference is preserved in `history/reviewed-export18/`, manifest
`c9e1e20710bb5f947ad47fa62328cebffb099fd3832d22909056bf8f1867cc76` (2026-10-09 07:46:39 UTC).
Its **288 pass / 2 fail / 18 info**, six scoped HDMI passes, 332 clear FPS material checks plus nine clear non-material diagnostics, two declared CSI cylinders, and 201 rigid power-service poses / 625 queries are historical evidence for that geometry. They are not automatically current passes for the revised tub or plenum. Alternative export18 reports remain historical. Fresh shadow-plenum Fujinon and original-storage exports, meshes, envelope and core-void comparisons now bind their own manifests; compact-Kowa service results do not transfer. See the [comparison and its limits](REVIEW.md#2-size-comparison-and-its-limits).

The frozen export18 raw failures are the active cooler/source-Pi overlap witness, **79.902671 mm³**, and the obsolete right-wall ray through the intentional CSI opening. The ray does not measure adjacent wall thickness. The frozen supplement's three adjacent 2.5 mm measurements describe the old wall. The new checker treats X−80/Z50 as an expected-empty CSI aperture test and separately probes the outer skin and original wall at X−110/Z50. Read its new manifest-bound result for the current count; the old 288/2/18 report remains preserved. Correcting this test context does not resolve the actual cooler/source conflict. Actual cooler profile and registration remain unresolved. Source Pi geometry retains 149 overlapping named-component solids; the raw sum is not occupied material, and the older 11.669 mm³ Boolean-difference witness is not an established lost-material volume.

The complete camera FPC and EVF feed remain unplaced. Storage plug clearance is a non-material reservation and does not establish actual mating. The intact 300 mm HDMI ribbon is retained; the fragile 200 mm study remains rejected. Both 270 mm power-path budgets include unresolved pad-root allowances, and the positive includes the 20 mm rigid fuse/joint zone. These are finished-path allocations, not copper-cut instructions. Complete flexible withdrawal, retained slack, hand/tool access and all physical tests remain STOPs. All 56 inherited gates and M1 remain open.

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
- Existing 1/2-inch switch-nut spanner/socket, saw/file, calipers/depth rod and soft-jaw vise
- Flat steel rule/bar, paint pens, fine smooth-jaw pliers, paper knob shims, panel prop/support and optional mirror
- Printed collar centring gauge, separately counted as a tool
- Current-limited bench supply, official Pi PSU, scope, logging USB power meter, electronic load and suitable charger
- Existing insert-repair tools and the camera tripod-block screw driver as a one-time bench exception

Provisionally allocate four existing-class 2.5 mm cable ties to separate red/black pigtail slack loops at the new carrier
lacing slots. Use them only if measured band thickness is ≤0.7 mm and head/tool clearance is proven. They must
not contact or press on the UPS PCB. This is an allocation from the baseline tie pack, not four extra packs.
Exact retention may change. Fixed tied folds cannot unfold for service; prove pack-disconnect reach with the
retention installed, without relying on opening a powered body first.

The new power-switch nut may require a suitable thin spanner. Measure its across-flats and approach first; use
an existing tool if it fits. This is a provisional extra tool, not a verified fit or a reason to omit the nut.
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

### B0. Supported optical setup

Keep the camera on its tripod block in a suitable clamp and support the lens separately while measuring. Never
react lens-thread torque through the PCB or cover. Confirm C-CS adapter seating and retain witness marks across
adapter/BFAR and BFAR/housing. Measure infinity back focus, rear-cell/filter clearance, camera cover reach and the
lens's usable support band. Record actual values; the CAD optical pose is not an infinity calibration.

Remove the heavy lens after measurement while the camera remains properly supported. Remove and bag the camera
tripod block and its two screws as the baseline B0 procedure requires. Keep the C-CS adapter correctly seated.
Do not print/freeze a collar before these dimensions and the revised M1/collar load requirements are settled.

### B1. Printed components and inserts

After the print holds are closed, inspect and slice the nominated part set: compact has nine production parts; original storage adds the sleeve.
The horizontal optical and EVF bores require a declared support and slicer review; do not assume a support-free tub.
Inspect the separate cold/hot plenums, roof bridges and integral posts for sag, incomplete bonds and support debris. Check all four edge mouths and both banks of inner-wall slots with a representative plenum coupon before a production tub. The 6 mm gap is not a bridge span. Keep the outer skin on the declared bed face; verify actual toolpaths and do not enable inaccessible internal supports. The deeper CSI tunnel must remain straight and open. Remove accessible supports without damaging the skin/posts, optical datums, carrier ears or screw seats. Do not drill out the deleted panel grooves: the selected panel is plain 2.8 mm. Check the selected
lens's collar and separate centring gauge. Install the three short tub inserts and one long collar insert under
the coupon-validated process, on the bench before electronics are present. Verify no insert enters an optical,
board or wiring clearance. No hood, Pi keeper or printed power plunger is used.

### B2. Electrical and stack preparation, fully unpowered

1. Identify the actual Pi 5 J2 pads from the official drawing and board itself. Prepare the removable signal
   pair with one half soldered to the two J2 pads and the other to the two power-switch terminals. Insulate and
   strain-relieve all four joints. Confirm normally-open operation and continuity before power; never wire the
   switch into the battery current path. Use the conditional Molex 2181120201/2181110202 pair in the BOM (28 AWG, two black wires per half). Exact pad access, full connector placement, wire cuts/stow and mating access remain hold points. Label J2 separately from FPS, continuity-test each conductor, and do not infer unlimited service life from the 30-cycle tin-contact rating.
2. Buy one 914.4 mm stock length of 16 AWG wire per colour. **Positive 270 mm is a finished-path allocation
   including a 20 mm rigid fuse/joint-sleeve zone.** Determine and trim actual copper cuts and solder overlaps
   to that finished path; do not cut 270 mm copper and then add a fuse. Both 270 mm total path budgets include unresolved
   pad-root allowances; they are not extra length to add later. No exact production cut or offcut is established. STOP until
   complete stored/extraction paths and joint allowances are proven. Conservatively charging both as 270 mm
   copper gives 0.142811 V at 8.6 A with copper at 60°C, leaving only about 7.2 mV to the unchanged G-W5 limit
   before hot fuse/contact/pad uncertainty. This nominal estimate is not a hot-test pass.
   Retain the pack's 60 mm 18 AWG lead and the near-XT30 positive inline fuse. Solder/insulate under the baseline
   fuse-temperature rules. Verify polarity and absence of shorts. Use the measured X1203 battery pads and
   neutral-cure RTV strain relief; do not move an assumed pad to make a route work.
3. Prepare the baseline EVF feed, 18/24 lead and QT lead. QT remains 250 ± 10 mm made from the two source leads;
   meter pin numbering instead of matching wire colours. Its four staggered splice joints need a new straight,
   accessible location in the vertical route. Do not import obsolete baseline absolute stow coordinates.
4. Bridge encoder A0 for address 0x37. Map the run, 18/24 and QT header leads before the stack becomes enclosed.
   Use the baseline pin mapping: QT physical pins 1/3/5/6, 18/24 pins 33/34, run pins 37/39. Do not substitute J2
   for a GPIO header pin or count the new button as a record control.
5. Fit the Active Cooler once and keep its native fan lead with the stack. Assemble Pi, X1203 and the four actual
   standoffs at their original spacing. Retain four upper M2.5 × 5 screws. Replace the four lower M2.5 × 5 screws
   with four M2.5 × 8 through the carrier; bag the removed four. The head recess leaves 3 mm of carrier material,
   giving 3.4 mm nominal engagement beyond the 1.6 mm PCB. Measure thread depth and bottoming before tightening.
6. Test the stack only under the authorized inherited bench-gate procedure, then shut down/disconnect all power
   again. Fit the OS microSD on the bench before carrier insertion; it travels with the complete stack. Keep
   recording storage out for insertion. Routine service removes this whole
   assembled module; it does not repeatedly disturb cooler clips, thermal pads or pogo-pin geometry.

### B3. Control panel and EVF subassemblies

Use the conditional CK1044 selection. Identify and retain the separate nut, mounting washer (receipt inclusion gate) and stop/tang washer. Set the stop for two adjacent 30° detents; continuity-test A and throw 2 for open/high 18 and closed/low 24. Preserve that stop-ring setting during service. Measure and cut its shaft from the new panel's actual knob projection;
do not reuse the old absolute Y cut value. Mount the encoder in its cradle. The FPS switch is independently supported and stays with the carrier/harness during service; its inline pair is mated on the bench. Seat the panel over its bushing and locating peg only after the source-bound support/clearance check, then fit its mounting washer and nut and check anti-rotation. Fit the two knobs with the retained paper-stop-shim method. Keep exposure and frame-rate
markings minimal and legible. The sole replacement power switch has “power” engraved above it; no indicator is added.

Fit the Adafruit 1505 only after confirming thread length, nut/washer and tool reach through the real panel.
The panel is 2.8 mm thick, inner Y25.2 and outer Y28. Its flange seats at Y28, centre X−20/Z25.5,
and the power nut bears on Y25.2. Protect the back terminals; do not use the unverified nut cylinder as
a hardware specification. Keep its signal-junction half free and accessible for later detachment.

Prepare the EVF emitter, native flex and board as the qualified baseline optical module; adhesive foam rides
with the OLED. Keep contact orientation and ZIF latch operations as the real kit requires. Fit the 3557 right-angle Pi head, 3556 straight EVF head and selected intact ribbon
only with power absent and verified matching orientation. Both compact and original storage now conditionally use intact 300 mm 3562;
200 mm 3561 is a rejected study at quantity zero. Physical R3 bend capability, thickness, connector clocking and EMI remain gates. Support adapter bodies and provide
strain relief; do not pull on the ribbon or treat a friction connector as retained without a test.

### 1. Base/grip and tub

Install the tripod nut and run button in the retained grip. Feed its run lead through the appropriate floor
passage while access is open. Seat the tub on the keyhole tongues and engage the independent grip-lock PT screw.
The lock is shifted 2 mm in Y, and upper strap anchors shift 12 mm in Y and 18.5 mm rearward in X. Check the actual
strap and lock clearances; the panel must not be the only thing preventing grip release. The pack remains out.

### 2. Camera first, carrier absent

Fit the camera/C-CS adapter through the open +Y side using the reviewed camera insertion sequence. The nominal
CAD motion approaches with a small rearward and upward offset before seating forward on the lip; exact sampled
motion evidence and real finger/tool access still require qualification. **Do this before the Pi carrier is
installed.** Do not claim that a camera can be forced past the vertical stack.

Fit and centre the lens collar with the printed gauge and three anchor screws/washers at the provisional
qualified cap. Use the integral roof's metal-tab torque catch, rather than the deleted hood catch, only after
its actual engagement is verified. Follow the inherited floating-camera/optical support rules. Do not leave a
heavy lens cantilevered from an unsupported camera. Lens final installation can wait until step 7.

### 3. EVF module

Slide the qualified OLED/board assembly into its real seats from +Y, with foam/flex unstressed and the eyepiece
correctly supported. Mate the EVF HDMI head from the reviewed direction with access to the connector body.
Do not bend the ribbon to compensate for a wrong head orientation. Establish the removable EVF power junction
and retain access to both housings. Final panel clamping happens later; do not let the unclosed module fall.

### 4. Insert the complete vertical carrier/stack

Preconnect the Pi HDMI head and wall-facing GPIO housings on the bench. Keep the EVF HDMI end free;
carry the complete FPS harness mated, with the FPS switch and carrier separately hand-supported. Stage
other Pi-end leads only under the verified insertion harness plan. Feed the camera pigtail only through the qualified source-driven swept passage, without scraping the
pair, single inline fuse or XT30 body. The local 3 mm corner relief retains 203.5/208 mm² nominal rear tongue
footprint; actual printed strength/wear remains gated. Use the current source/export rather than the obsolete
simple rectangular pocket dimensions. Outer grip, battery and cap dimensions remain unchanged.
Bring the complete carrier, Pi, cooler, UPS and kit hardware in from +Y, then seat it onto its two mounting
bosses. The Z69 rear post and diagonal arm solve the modeled USB 5 V adapter collision. Confirm actual hardware
and full harness occupancy against the current export; do not force the adapter aside. Install the two carrier
PT screws only under the qualified assembly sequence. No cooler removal or pogo-interface redesign is part of this action.

Keep the recording stick out: its −X removal axis and projecting housing must not be trapped during +Y carrier
movement. The bench-fitted microSD remains with the carrier. Ensure the camera was installed in step 2.

### 5. Internal connections and slack

The selected 12 × 27 mm R1 CSI side slot has 323.14 mm² nominal opening; both declared cylinders clear export18 solids. Actual latch/FPC operation remains on HOLD.
STOP until actual latch/jaw dimensions, operation and FPC occupancy in those corridors are demonstrated.
Connect the camera FPC only while fully unpowered. Check both end contacts/latches, full ribbon width and all
folds; preserve the entire purchased 200 mm cable with honest slack storage. Mate HDMI, USB EVF power, native fan
and header leads by their bodies. All individual header sockets must match physical pin numbers and be seated
straight, then gently tug-tested.

Route and secure the 16 AWG pigtail, pack lead, run lead, QT, 18/24, J2 lead and EVF wiring within qualified lanes.
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
and not installed. The refreshed full 300 mm exact study binds the selected shadow-plenum manifest and records 6 scoped passes / 0 failures. The old
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

For the FPS GPIO connection, use two measured female-ended stubs cut from an Adafruit 1950 pack,
not an unspecified Dupont-to-PH lead. The pack contains twenty 150 mm female/female 2.54 mm jumpers,
28 AWG; retain one female head on each of two coloured leads, leaving eighteen intact workshop spares.
Join the retained stubs to the selected PicoBlade male tails with two solder splices and two sleeves.
Final cuts, overlaps, head/insulation dimensions and the complete FPS route remain hold points; do not
install the full purchased wire length by assumption. No new crimper is required.

### 6. Close the control panel

Support the panel on a stable prop, not its wires. The 18/24 pair stays mated with the supported switch/carrier assembly; it is disconnected only on the bench. Mate the QT and J2 junctions with both housings accessible before seating the panel. Service reach/slack for this pose must be
measured; the baseline 60 mm prop offset is a starting target, not an inherited fit result.

Move the panel inward along −Y without rotating it into the camera, EVF or stack. Confirm its camera catch and
EVF clamp engage without pinching anything. Confirm the tub bosses contact the panel pads at Y23.5 with no
nominal seating gap; the face plate spans Y25.2..28. Tighten the four panel PT screws to the validated limit. There is
no hood to snap down and no hood-release pin operation. If slack cannot stow without force, stop and re-route.

### 7. Media and lens

The OS microSD was fitted on the bench before carrier insertion. **Do not insert or withdraw it with the
panel closed:** its +X path intersects the panel-mounted power-switch body. Insert the selected recording drive straight along +X into the upper USB3 port: compact Princeton PHD-USSD-500G or original
SDCZ880 with its own 185 mm body and sleeve. Remove and bag the Princeton cap first. Its published 34 × 15 × 7 mm
size includes that cap; the model conservatively reserves the full 34 mm outboard X−122..−156 plus an assumed
mating plug in the unchanged compact body. Verify real identity, fit, Linux/USB compatibility, bus power and
warm sustained ≥100 MB/s operation; vendor maximum speed is not a bench result. FIT Plus remains studied and
unadopted. Never install two drives or use the long SanDisk drive in the short enclosure.

Install the lens only with the collar/support system already carrying it. Check both optical witness marks.
Never hold the PCB/cover to react thread torque. Verify the metal-tab catch and inherited floating-camera seating
method. The pinch screw is the last lens operation, using its validated cap. Recheck infinity/back-focus and
support after any collar or adapter change; do not substitute visual centring for optical measurement.

### 8. Pack last and qualification

Before reconnecting, inspect polarity, insulation, physical connector seating, free fan, clear vents, secure
strap/lock and unobstructed controls. Only after closure and required bench checks, mate the XT30 by its housings,
place the pack and slack/fuse safely in the grip, then close the cap. Never force the cap against the fuse or leads.

Run inherited closed-body electrical/workload/thermal/recording gates, including the unchanged 8.6 A and ≤0.15 V
pack-to-pads test, the fuse/contact temperatures, Pi rails and resets, warm ≥100 MB/s storage, EVF stability and
zero dropped frames. The swept floor passage adds body/grip air communication, and the unchanged CSI slot remains an unsealed bypass. Measure closed-body airflow/temperature with hand and strap in place, including rear/underside intake and front/underside exhaust mouth occlusion. Gross mouth or inner-slot area alone does not establish cooling. Record unobstructed, normal-hand, fitted-strap and stand/support positions as separate powered qualification cases. A blocked hot underside mouth leaves only 210 mm² front opening versus 510 mm² hot wall slots; do not credit the 534 mm² gross outlet sum or infer rated operation with a blocked vent. Re-evaluate battery temperature, fan clearance and pressure loss. Re-run the revised collar, relieved tongue and strap
load/service tests. A J2 shutdown does not end the need
to disconnect the pack before reopening. Record measured results; no gate is closed by this written plan.

## 5. Service routes

All routes begin with section 1, including physical pack disconnection and removal of external power.

| Service target | Required order and movement |
|---|---|
| Control panel | After battery isolation, remove the FPS knob, retaining nut and mounting washer while supporting the switch; preserve the stop/tang washer and its indexed setting. Remove four panel PT screws; support and translate +Y over the released FPS shaft/bushing/peg only as far as verified clearance/slack permits. Disconnect J2 and QT by their housings. FPS switch and mated inline pair remain with the carrier/harness; no in-body FPS connector pull-out. Lift the detached panel away without hanging it from leads. STOP until this complete sequence is source-bound and physically qualified. |
| Complete Pi/UPS/cooler module | Remove recording storage along −X. Keep the bench-fitted microSD with the carried stack; any card withdrawal requires panel removal first. Detach the panel-side QT/J2 junctions and remove the panel while supporting the FPS switch. Disconnect HDMI at the EVF end and EVF power at its inline junction; keep the Pi HDMI head and wall-facing GPIO housings mated. Release the camera FPC at the Pi only through qualified latch access. Free the already-isolated battery pigtail/fuse from the grip passage under the verified retention/release procedure; fixed tied loops cannot be assumed to unfold. STOP until actual FPC release, complete pigtail withdrawal, run-lead reach and every other fixed-to-carried lead have been proven. Remove the two carrier PT screws, then stage the carrier +Y with headers, native fan lead, Pi-mated full HDMI, separately hand-supported FPS switch and complete still-mated FPS harness in their checked relative arrangement. The tub rest/guide stay fixed. Disconnect remaining accessible junctions only in a supported, reach-qualified staging pose; bench-separate FPS only if needed. Never hang the switch or module from wires. Cooler and standoffs stay assembled. |
| Camera / adapter | Support/remove lens under optical rules; release the camera-end FPC and confirm it is fully free before any camera motion. Remove panel and complete carrier first where the reviewed clearance requires it. Reverse the camera-first insertion motion. Never pull the camera through the installed stack or react torque through its PCB. Refit camera before carrier. |
| EVF | Detach panel; unplug EVF power by both junction housings and HDMI by the adapter body using verified tool access; protect native flex, release panel clamp and slide module +Y. No ribbon pulling or forced fold. |
| Recording media | With recording ended and safe removal completed, extract drive straight −X through rear recess; do not rock the Pi receptacle. Physical pack-disconnect prerequisite applies whenever this is part of internal service. |
| microSD | Shut down and isolate all power. Remove the control panel under its supported service procedure before any +X card withdrawal; the closed-panel path is blocked by the power-switch body. Confirm actual panel-off tool/hand reach, or carry the card with the complete stack and service it on the bench. Preinstall the replacement card before carrier insertion. No cooler or PCB separation is required. |
| Grip/base | Pack out and XT30 parted; free run and pigtail leads before sliding the grip off its keyholes; release the independent grip-lock screw. Panel retention is not a substitute for that lock. |

Reassemble in reverse dependency order, with camera before carrier, junction access before panel closure and pack
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
[baseline wiring](../../../electronics/gs8-d2-v1/WIRING.md), [baseline handoff](../HANDOFF.md).
