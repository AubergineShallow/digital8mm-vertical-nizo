# D2 vertical Pi: review candidate

**Shadow-gap ventilation candidate.** A plain integral cooler-side skin at Y−35.6 conceals separate cold and hot outer plenums; the original wall remains Y−28..−25.5 and the inner cavity datum stays fixed. Rear/underside mouths supply intake, and front/underside mouths discharge exhaust. The compact core is now 158 × 63.6 × 100 mm. The control panel is plain 2.8 mm: its four former grooves had 0.2 mm blind floors and were not through UPS vents. Nine compact production parts and all purchased selections/quantities are retained.

**PRINT HOLD.** The front mouth removes the frame beneath the first roof layer over Z5..40. A nominal 10.7 mm distance there is not a two-ended supported bridge; raster direction may require about 35 mm of bridging. The expanded coupon contains this region. Freeze geometry for review, but do not release the tub for printing until slicer paths, bridge behavior and cleanout are demonstrated.

**USB and CSI source corrections retained.** EVF power remains at source-registered USB2 and recording storage at USB3. The 12 × 27 mm R1 CSI tool opening remains straight and unsealed through the deeper side structure. It is a bypass around the intended cooling path; no seal, dust/water rating or airflow performance is implied. Actual cooler registration, latch/jaw operation, the full 200 mm FPC and complete EVF feed remain on HOLD.

Status: **UNQUALIFIED REVIEW CANDIDATE, 2026-10-09. Not released, fabrication-ready or physically proven.**

This is a separate design candidate for review against the preserved upstream history. Baseline commit
`d38468e58eb2b02d56743e2e0cfdd8f780818a65` is preserved. Nothing in this directory authorizes procurement,
printing or replacement of the baseline production release. All 56 inherited physical gates and M1 remain open.

## Current checkpoint: unresolved assembly STOPs

The current compact-Kowa export is a shadow-gap plenum candidate derived from reviewed export18. The earlier visible angled-channel trial is preserved in `vent-study/angled-channel-trial/` as a rejected visual alternative; its dimensions, throat values and 75 geometric passes do not validate the plenum. The selected manifest and `shadow-plenum-checks.json` live in `out/compact-kowa_lm6hc/`; the source geometry is `vent_geometry.py`. New evidence is valid only for the manifest hash recorded in that report. Re-export or source changes require rebinding, not reusing old pass counts.

Current selected manifest `53e668d43847acd1f59d2b559a562476c54a23db0918debd482d632f0e8ceb77` has **292 pass / 1 fail / 18 info** in the main audit. The failure is the retained **79.902671 mm³** cooler/source-Pi conflict. The separate plenum report has **49 pass / 0 fail / 21 info**; current HDMI has six scoped passes, FPS has 332 clear material checks plus nine clear non-material diagnostics, and rigid power service has 201 poses / 659 exact queries with no hits. The declared CSI cylinders and static power-wire checks pass their narrow geometric scope; actual CSI operation stays on HOLD. The new dedicated USB-head report passes the bounded installed-head reservation against the complete current tub and accepted support-source hashes. The earlier missing-extract attempt remains historical. Received overmold/exit, full EVF feed and actual service still remain unqualified.

The frozen export18 reference is preserved in `history/reviewed-export18/`, manifest
`c9e1e20710bb5f947ad47fa62328cebffb099fd3832d22909056bf8f1867cc76` (2026-10-09 07:46:39 UTC).
Its **288 pass / 2 fail / 18 info**, six scoped HDMI passes, 332 clear FPS material checks plus nine clear non-material diagnostics, two declared CSI cylinders, and 201 rigid power-service poses / 625 queries are historical evidence for that geometry. They are not automatically current passes for the revised tub or plenum. Alternative export18 reports remain historical. Current shadow-plenum alternatives have fresh export, mesh, assembly-envelope and core-void evidence as described below; selected compact-Kowa service results do not transfer to them.

The frozen export18 raw failures are the active cooler/source-Pi overlap witness, **79.902671 mm³**, and the obsolete right-wall ray through the intentional CSI opening. The ray does not measure adjacent wall thickness. The frozen supplement's three adjacent 2.5 mm measurements describe the old wall. The new checker treats X−80/Z50 as an expected-empty CSI aperture test and separately probes the outer skin and original wall at X−110/Z50. Read its new manifest-bound result for the current count; the old 288/2/18 report remains preserved. Correcting this test context does not resolve the actual cooler/source conflict. Actual cooler profile and registration remain unresolved. Source Pi geometry retains 149 overlapping named-component solids; the raw sum is not occupied material, and the older 11.669 mm³ Boolean-difference witness is not an established lost-material volume.

The complete camera FPC and EVF feed remain unplaced. Storage plug clearance is a non-material reservation and does not establish actual mating. The intact 300 mm HDMI ribbon is retained; the fragile 200 mm study remains rejected. Both 270 mm power-path budgets include unresolved pad-root allowances, and the positive includes the 20 mm rigid fuse/joint zone. These are finished-path allocations, not copper-cut instructions. Complete flexible withdrawal, retained slack, hand/tool access and all physical tests remain STOPs. All 56 inherited gates and M1 remain open.

## 1. Design intent and what changed

The Pi is actually vertical: Pi 5, Active Cooler, X1203 and their standoffs move as one rigid assembly under
`(x, y, z) -> (x - 28, 22.2 - z, y + 39.3)`. Its PCB plane is XZ, not the old horizontal XY plane.
The inherited stack spacing and pogo-contact relationship are retained in the model; the actual cooler
outline and registration remain unqualified. Source-registered Pi connectors replace the old port proxies.
A separate open carrier supports the assembly; service does not require taking the cooler off repeatedly.

The exterior follows Braun Nizo simplicity: a narrower satin-silver main body, restrained black lens collar and
handgrip, an integrated roof, and one removable control side panel. There is no separate hood, mechanical power
plunger, ornamental badge or added display. The existing silent-film/no-audio scope and minimal controls remain:
record/run, exposure encoder with push, physical 18/24 selector, power button and EVF. The word “power” is
engraved above the sole replacement switch. No LED/light-pipe or indicator addition.

| Feature | Preserved / revised |
|---|---|
| Lens axis | Preserved at Y = 0, Z = 60 mm; optical seating and C-CS relationship remain measured gates |
| EVF axis | Y = 11, Z = 78 mm; emitter, board and eyepiece relation retained as an optical module |
| Core | Shadow-gap compact: 158 × 63.6 × 100 mm; reviewed export18 compact: 158 × 56 × 100 mm. The current original-storage alternative is 185 × 63.6 × 100 mm. |
| Pi stack | Rigid 90° roll and relocation; real separate carrier with four stack fasteners |
| Side panel | Plain 2.8 mm plate; the four blind grooves are removed. Plate inner Y25.2 and outer Y28; four accessible PH1 PT fasteners; extraction along +Y; tub bosses meet panel pads at Y23.5 without a seating gap |
| Stack carrier | Two PH1 PT fasteners; whole Pi/cooler/UPS assembly stages +Y after required fixed-side junctions are released. Pi HDMI, headers, microSD and the supported mated FPS harness remain carried. |
| Grip/battery | Outer grip, pack and cap dimensions retained; local upper grip-web pocket and revised pigtail passage; independent grip lock shifts 2 mm in Y |
| Strap | Upper attachment features move 12 mm in Y and 18.5 mm rearward in X; new strap/access checks required |
| Camera | Installed before the carrier; no claim the camera can pass through an already-installed stack |
| OS microSD | Bench-fitted before carrier insertion and carried with the stack; service only with panel removed or on the bench. Closed-panel +X extraction intersects the power-switch body. |
| Lens collar | Revised exterior radius and anchor span; load/clamp qualification must be repeated; M1 remains open |

### Pi representation correction

The cached fused Pi shape did not reliably retain its source components. Independent point classification
found all 90 sampled interior points per CSI connector outside the cached union, while the nine sampled
Ethernet points were inside even though a Boolean-difference operation produced an Ethernet witness. The
reported 11.669 mm³ aggregate difference therefore is **not** an established volume of lost material. These
finite point samples diagnose membership at those points; they are not a whole-volume equivalence proof.

The export18 repair preserves all 149 named-component solids as an overlapping assembly instead of applying
the unreliable fusion; all 189 previously sampled source-interior points are now inside the saved Pi assembly.
Its raw sum of component-solid volumes must be labeled as a sum, not occupied material; the Pi row's occupied-material volume is left unset. A conservative core-void interval bounds
remaining component material without reporting the overlapping raw sum as occupied volume. No source contacts are removed to clear an interference.
The three manifest-bound exports pass source/file identity checks and have fresh assembly-bound comparisons.
The reported core-void intervals remain proxy-volume bounds; the approximate cooler and actual
interface/thermal gates remain open regardless of this representation repair.

## 2. Size comparison and its limits

| Main-body rectangular envelope | L × W × H, mm | Envelope, cm³ | Difference from baseline |
|---|---|---:|---:|
| Baseline D2 | 154 × 70 × 100 | 1,078.0 | Reference |
| Frozen export18 compact | 158 × 56 × 100 | 884.8 | −17.9% |
| Shadow-gap compact, either lens | 158 × 63.6 × 100 | 1,004.9 | −6.8% |
| Shadow-gap original storage | 185 × 63.6 × 100 | 1,176.6 | +9.1% |

The shadow-gap compact core is 9.1% narrower and 4 mm longer than baseline. It adds 7.6 mm outside the reviewed Y−28 wall; the interior datum stays fixed. The earlier 59 mm angled-channel body was rejected because its slot mouths remained visibly exposed. Core figures exclude the lens, eyecup, controls and grip.

The fresh [untessellated STEP comparison](out/comparison/assembled-comparison.json) includes every modeled assembly part. Values below are rounded to 0.1 mm and approximately 0.1%; the rectangular bounding envelope is not occupied material or measured product volume.

| Full assembly | L × W × H, mm | Bounding envelope, L | Difference from matching baseline |
|---|---|---:|---:|
| Baseline Kowa | 244.8 × 79.4 × 216.8 | 4.213 | Reference |
| Shadow-gap compact Kowa | 248.8 × 72.8 × 216.8 | 3.926 | −6.8% |
| Baseline Fujinon | 239.2 × 79.4 × 216.8 | 4.117 | Reference |
| Shadow-gap compact Fujinon | 243.2 × 72.8 × 216.8 | 3.838 | −6.8% |
| Shadow-gap original storage, Kowa | 275.8 × 72.8 × 216.8 | 4.352 | +3.3% |

The original-storage full envelope is larger than baseline. The frozen export18 compact-Kowa full bounding box, 248.8 × 67.2 × 216.8 mm and roughly 14% lower bounding volume, remains historical. Source mesh bounds and untessellated STEP bounds are different measurements and retain their stated provenance.

The current comparison binds compact Kowa `53e668d4`, compact Fujinon `c31096ed` and original-storage Kowa `ecb18336`; full hashes are recorded in the linked report. All three have current source/file identity and print-mesh checks. Their modeled mass/centre-of-mass and envelope comparisons are available there. The alternatives have no refreshed complete service/harness audit; compact-Kowa results must not be transferred to them.

Conservative empty-model core intervals are **672–689 cm³** for [compact Kowa](out/comparison/volume-compact-kowa_lm6hc.json), **673–691 cm³** for [compact Fujinon](out/comparison/volume-compact-fujinon_hf6xa.json) and **805–823 cm³** for [original-storage Kowa](out/comparison/volume-original-kowa_lm6hc.json). These include intended plenum/cooling air, cable and service space and omitted details. They are proxy-representation bounds, not removable waste or measured cavity volumes. The overlapping Pi source-solid sum must never be subtracted as if it were occupied union material.

Mass remains a planning estimate from component proxies and empirical printed-density/infill factors, not a weighed camera. The legacy XT30 row includes a 12 g connector/fuse/pigtail lump at its rigid proxy; other harness masses and the actual distributed wiring centre of mass remain unresolved. The additional skin/plenum stock and restored panel material change housing loads even though the carrier, grip and J4 joint geometry are retained. See [the concealed-vent structural supplement](structural-review/CONCEALED-VENT-STRUCTURAL.md) for current manifest-bound mass and load sensitivity. Old whole-tub zero-difference bindings do not apply to this changed tub.

### Concealed airflow passages and physical holds

The broad outer face has no ventilation slots. Front and rear edge mouths remain visible in direct edge views; this conceals the broadside grilles, not every opening from every angle. It is a 1.6 mm integral skin at Y−35.6..−34, with a 6 mm plenum gap to the original outer wall at Y−28. The original 2.5 mm wall and inner Y−25.5 datum remain. A divider separates cold and hot outer bays. The required straight CSI service opening remains visible and open through the deeper side structure; its surrounding tunnel isolates the adjacent bay locally without sealing the access opening.

Nominal geometric areas from the source are:

| Feature | Gross area, mm² | Definition |
|---|---:|---|
| Cold internal wall passages | 420 | Four 35 × 3 mm slots into the retained inner cavity |
| Cold rear edge mouth | 420 | 6 mm plenum gap × 70 mm height |
| Cold underside edge mouth | 426 | 6 mm gap × 71 mm length for the compact body |
| Hot internal wall passages | 510 | Four 42.5 × 3 mm slots into the hot outer bay |
| Hot underside edge mouth | 324 | 6 mm gap × 54 mm length |
| Hot front edge mouth | 210 | 6 mm gap × 35 mm height |
| Separate CSI service opening | 323.14 | Straight 12 × 27 mm R1 opening; unsealed bypass |

These are gross opening areas, not a demonstrated minimum hydraulic section, useful flow rate or cooling result. Internal posts, turns, junctions, the bay divider, actual cooler fan offset and occlusion add resistance. Rear/underside inlet areas and front/underside outlet areas are parallel mouths into their respective bays; their sums are not available at every internal section. The saved-STEP report measures a smallest sampled hot horizontal section of 299.4 mm², below both the 534 mm² gross hot-mouth sum and 510 mm² wall-slot sum. This is the minimum among the named sampled sections, not a proven global hydraulic minimum. The earlier angled-channel normal-throat values do not apply to this plenum.

Integral 1.6 mm-diameter posts on a nominal 8 mm grid support the plenum roof, with source-defined omissions and additional placements around openings. Nominal grid spacing is not a verified maximum bridge span. The outer face is the print bed face; the original side wall becomes a roof over inaccessible internal gaps. Slicer toolpaths and representative plenum coupons must establish bridging, post continuity, sag, opening area and cleanout. Automatically generated supports that cannot be removed through the real mouths are unacceptable; no support-free claim is made. Optical and EVF bores retain their own support review.

A preliminary regular-grid open-edge coupon is generated from the selected tub at X−152..−104 / Z8..40, with a [source-bound receipt](vent-study/shadow-plenum-coupon/receipt.json). Its STEP/STL exist and its saved STEP is valid; it is not print-released, sliced or tested. Its accessible cut edges do not establish closed-body cleanout, and it omits ports, the CSI sleeve and several post exclusions. The second generated crop is X−110..0 / Z0..100, nominal 110 × 100 × 10.1 mm, covering front/top edge spans, the lower support row, both wall-port banks and the CSI sleeve. Its [receipt](vent-study/shadow-plenum-coupon/port-service-receipt.json) and the [two-coupon index](vent-study/shadow-plenum-coupon/coupon-index.json) bind both STEP/STL pairs to the selected tub. Both saved STEP crops are valid single solids; neither is print-released, sliced or tested. The expanded crop omits the rear region and complete cold-rear mouth, so it does not establish a global maximum unsupported span. These two plenum coupons remain separate from the production nine and prior nine structural coupons.

The saved-STEP topology check separates three external voids, cold bay, hot bay and CSI sleeve, within its external test domain; it excludes the main cavity. This external bay separation does not seal the main-cavity airflow path. The existing internal separator/baffle and floor communication to the grip remain, and the CSI aperture is unsealed. No sealed cooler duct or ingress rating is claimed. The former four panel reliefs were blind grooves with 0.2 mm floors and supplied no modeled through-vent area; their removal restores a plain 2.8 mm panel. The skin, divider and posts are part of the tub, with no loose cover, additional fasteners or purchased fan/mesh/seal/duct component.

Measure the real cooler and fan offset, inspect the complete printed plenum, test hand/strap and surface occlusion of every edge mouth, and run closed-body workload and battery-temperature tests. The deeper CSI tunnel also needs the actual latch/jaw/FPC test. Actual cooler fit and thermal performance remain separate HOLDs.

Keep powered occlusion cases distinct: unobstructed reference, normal hand positions, fitted strap positions, and stand/support contact positions. If the underside hot mouth is blocked, only the 210 mm² front mouth remains against 510 mm² of hot wall ports, before internal losses; the 324 + 210 mm² outlet sum cannot be credited. Any controlled occlusion experiment belongs to the inherited thermal qualification program. No rated operation with blocked mouths or minimum useful airflow has been established.

### Corrected rotary-switch source hold

The inherited CK1049/6.35 mm D-shaft description was inconsistent with Lorlin’s ordering table and its
Ø25 × 13 mm body proxy was undersized. The conditional corrected selection is CK1044: imperial 6.35 mm
shaft with 5.5 mm across-flat, PCB terminals, BBM, one pole, adjustable stop and 30° indexing.
Its body is Ø27.5 mm, 14.1 mm behind the mounting face, with all 13 pins reserved to 18.1 mm rearward.
The concealed-vent candidate retains export18’s switch centre at Z80 and 24 mm knob; fresh scoped FPS and HDMI reports now bind the selected shadow-plenum manifest; actual service remains unqualified.
Earlier `e8648073` results are the preceding checkpoint and do not validate this correction.

Stock shaft length is 38 mm from the mounting face, with a 30 mm end flat. The proposed 11.8 mm cut leaves
about 3.55 mm flat engagement after the 0.25 mm bushing-clearance allowance; actual stack, coupon fit and
removal force remain gates. Retaining nut, mounting washer and adjustable stop/tang washer are separate
planned pieces; mounting-washer inclusion and all hardware dimensions require receipt checks. Preserve the
stop ring during service. Verify common A/throw 2 gives open/high 18 and closed/low 24 before applying labels.
See the official Lorlin drawing and separate stop-washer source linked in the BOM.

Selected FPS service keeps the inline pair mated and carries the supported switch and complete harness with
the carrier. Remove the knob/nut/mounting washer before the panel slides over the shaft, while preserving
the stop ring; disconnect the pair only on the bench. This supersedes in-body pair draw-out proposals.
The current nominal main axis is 200.000 mm including donor stubs; switch branches A95.4644 mm and
throw2 102.4759 mm precede unresolved solder allowances. These are route-study lengths, not cut instructions;
the refreshed selected report records 332 material checks with zero hits plus nine separate clear non-material
reservation diagnostics, bound to the shadow-plenum manifest. Its source receipt is `out/fps-service-study/fps-final-source-receipt.json`. Actual
roots, hand support, complete neighboring loom and physical service remain unqualified.

## 3. Part and assembly trade-offs

- Compact: nine installed printed parts: tub, panel, carrier, base/grip, battery cap, eyecup, two knobs and lens collar.
  Original storage adds the tenth part, the existing stick sleeve. Baseline had twelve.
- Body PT screws remain seven: four panel, two carrier and one grip lock. This is a part/form simplification,
  not a claim that the body uses fewer screws.
- Collar hardware remains three M3 × 10 plus one M3 × 16 PH1 screws, four washers, three short and one long insert.
- Stack hardware remains four supplied standoffs and eight installed M2.5 screws. Four upper M2.5 × 5 are retained;
  four lower ones are replaced with M2.5 × 8 through the carrier. The four removed screws are bagged, not installed.
- The 4 mm carrier bosses have 1 mm head recesses, leaving 3 mm between head bearing and the 1.6 mm board.
  Nominal engagement is 8 − 3 − 1.6 = 3.4 mm. Actual standoff thread depth, head fit, bottoming, board support and
  assembly torque must be measured. The earlier unrecessed 2.4 mm engagement is not this candidate's intended state.
- An electrical signal switch and removable two-pin lead replace the printed mechanical power linkage. This
  adds purchased parts and four solder joints. The side panel can then be detached without desoldering.
- Two HDMI adapters and one ribbon replace one molded cable, net two additional purchased pieces.
- There are eleven functional harnesses, including the native/included leads, versus ten at baseline.

The generated [BOM](BOM-VERTICAL.md) and [CSV](BOM-VERTICAL.csv) preserve the full baseline procurement/tool scope
with explicit revised, optional and removed lines. Installed parts, kit contents, purchase amounts and spares
are separated. The complete planned solder count is **24** with the supplied pack male, spliced QT lead,
two FPS donor splices and preterminated J2 pair. The legacy twelve-joint tally omitted four QT joints and
two camera-side XT30 female terminations; the candidate adds four J2 joints and two FPS donor splices.
Optional regulator work and a missing pack male are separate additions. The BOM has 131 rows, not 131
physical parts; its installed-category counts avoid double-counting included kit constituents.

## 4. Proposed component substitutions

### Recording storage

The compact primary is now Princeton PHD-USSD-500G, a USB-A 500 GB SSD. Its published 34 × 15 × 7 mm envelope
includes the cap. CAD reserves that full 34 mm outboard from port X−122 to X−156, plus a separate assumed mating
plug, through the intended rear opening of the unchanged 158 mm core. Remove the cap before insertion and bag
it. Approximate mass is 5 g; advertised maxima are 500 MB/s write and 600 MB/s read, with 0–70°C operation.
These claims do not close ≥100 MB/s warm sustained G-W10. Linux is absent from the vendor's supported-OS list;
actual Linux/USB compatibility, bus power, identity, dimensions, removal grip and availability remain gates.
[Princeton official specification](https://www.princeton.co.jp/product/storage/phdussd.html).

Samsung FIT Plus MUF-256AB remains a studied, unadopted alternative. Its up-to-110 MB/s advertised write figure
leaves little margin against the warm sustained requirement, so it is no longer the recommended compact choice.
[Samsung 2024 datasheet](https://download.semiconductor.samsung.com/resources/data-sheet/2024_Samsung_Data_sheet_UFD_FIT_Plus_v1.2_10139817901318.pdf).
The original SDCZ880 and 185 mm body remain the fallback; their physical and warm-speed gates also stay open.

### Power control

Adafruit 1505 is a normally-open black momentary switch connected across Raspberry Pi 5's two J2 pads through a
removable two-pin junction. It requests the same actions as the onboard button. It is not a hard battery isolator;
physical XT30 disconnection remains mandatory for internal service. J2 position in the route study is a hypothesis
until the actual board is inspected, not a measured pad datum. [Pi documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#add-your-own-power-button).

The panel switch centre is X = −20, Z = 25.5 mm, flange at Y = 28 mm. The reserve allows 29.4 mm behind the flange
plus 5 mm button height. The 2.8 mm panel spans Y25.2..28, and the nut bearing plane follows its inner Y25.2 face.
The tub bosses contact the panel pads at Y23.5 without a nominal seating gap. The vendor listing and drawing disagree; the model's Ø22 × 3 mm nut reserve is expressly
unverified. Thread length, nut/washer profile, rear terminals, insulation, anti-rotation and a usable nut-tool
approach must be checked with the real part. No nut access or panel-thickness pass is inferred from the cylinder.
[Adafruit 1505](https://www.adafruit.com/product/1505), [linked drawing](https://cdn-shop.adafruit.com/datasheets/R13diagram.jpg).

The lead provision is one preterminated matching two-pin pair, with two housings and four contacts included.
The J2 pair is conditionally specified as Molex 2181120201 (150 ± 6 mm female tails) plus 2181110202
(225 ± 6 mm male tails), both single-ended 28 AWG UL1061 black leads. Lengths exclude the housings.
A finished 150 mm per-conductor combined signal path remains a target, not a verified copper cut.
The nominal 9 × 4.25 × 3.3 mm mated reference body fits the estimated 6 × 8 × 12 mm reserve with mating
axis Z, but actual body/latch tolerances, mating travel, both wire roots, complete stow and pad access remain
unplaced/unqualified. Four solder joints remain. The polarized friction-lock family has no alternate keying;
label J2 distinctly from any matching FPS junction and continuity-test the black conductors. The official
wire-to-wire system specifies 1.5 A maximum for 28 AWG, 125 V and only 30 tin-contact mating cycles.
This is signal wiring only. Remove/bag bulky factory flags only after recording identity and replacing them
with small circuit labels; neither flag envelopes nor repeated service are cleared by nominal body fit.
See the linked Molex drawings/specification in `BOM-VERTICAL.md`.

### HDMI

The conditional primary for both compact and original-storage bodies is one intact Adafruit 3562 ribbon,
300 × 10 mm, with one 3557 right-angle Pi head (17.5 × 15 × 14.5 mm) and one 3556 straight EVF head
(26.5 × 17.3 × 4 mm). Each variant still uses three purchased HDMI pieces. The 200 mm 3561 study is retained
at quantity zero as rejected/fragile: its both-unplugged pose had effectively zero tolerance reserve.
Actual availability remains unverified. [3557 Pi head](https://www.adafruit.com/product/3557),
[3556 EVF head](https://www.adafruit.com/product/3556), [3562 primary ribbon](https://www.adafruit.com/product/3562),
[3561 rejected study](https://www.adafruit.com/product/3561).

The selected 300 mm compact routing input is retained in
[`routing-snapshots/hdmi-corrected-ports-20261009-0623`](routing-snapshots/hdmi-corrected-ports-20261009-0623/input.json).
The refreshed selected HDMI report records 6 scoped passes / 0 failures, bound to the shadow-plenum manifest. The historical four over-PCB
tool failures remain rejected diagnostics and are not the selected CSI path.
This printed-solid/material study does not certify the complete interacting flexible loom or real service. A developable 45° cylindrical fold avoids modeled edgewise stretch, but
physical R3 bending, actual thickness, connector clocking, all 10 mm of width, slack retention and service
extraction still require qualification. Supplier warnings about reduced durability/shielding remain relevant
for EMI/live-video and repeated-service testing. No purchased ribbon is shortened virtually to fit the model.

### Battery pigtail

The proposed camera pigtail uses red and black 16 AWG PRC high-flex copper wire purchased as one 914.4 mm stock
length per colour. Positive 270 mm denotes the **finished path including a 20 mm rigid fuse/joint-sleeve zone**.
Its flexible copper cut and solder overlap must be measured and trimmed to the finished path; do not add a
fuse to 270 mm copper and claim it fits. Both 270 mm total path budgets include unresolved pad-root allowances; they are not extra length to add later. Neither convention proves a production cut or an exact remaining offcut. The vendor
lists 3.0 mm OD; reserve 3.2 mm per core and a 6.4 × 3.2 mm pair. The pack's existing 60 mm 18 AWG lead stays.
[PRC wire](https://www.progressiverc.com/products/prc-silicone-wire-16-awg).

The planning calculation conservatively charges both paths as 270 mm copper and uses 13.17 mΩ/m per 16 AWG core, 21 mΩ/m per 18 AWG core, 4.46 mΩ cold fuse and 1 mΩ
XT30 contact estimate: 0.129789 V at 8.6 A. Raising only the wire resistance to 60°C gives 0.142811 V. These are
estimates using nominal copper properties and legacy contact assumptions, not measured PRC resistance or a hot
fuse/contact/pad qualification. The unchanged 0.15 V G-W5 ceiling leaves only about 7.2 mV in the wire-hot case, before additional hot fuse/contact/pad uncertainty.
The earlier 250 mm proposal cannot supply modeled service slack. The revised finished-path convention, actual
solder overlaps and pad allowance still require the combined source-bound snapshot and physical confirmation.
Actual pads, solder cups, bend space, stored slack, fuse sleeve temperature and grip extraction remain gates.
Do not enlarge the drop ceiling to fit a route.

The mechanical power revision integrates a **single** inline fuse in the frozen 21° yaw/45° pitch junction
pose, a source-driven swept floor passage and local 3 mm corner relief. It retains 203.5 mm² of the original
208 mm² nominal rear tongue footprint; this projected area is not a strength or creep qualification. The
passage is derived by [`power_geometry.py`](power_geometry.py) from the frozen power route. Earlier simple
rectangular passage/pocket coordinates do not fully describe the revised cut and are not a fabrication drawing.
Outer grip, battery and cap dimensions remain unchanged.

The refreshed saved-STEP power-service report records 201 rigid pack/junction/fuse poses and 659 exact
queries with zero hits, bound to the selected shadow-plenum manifest. That narrow study explicitly
leaves physical qualification false. Complete flexible-path deployment with the corrected finished-length convention, actual pad/pin exits, finger
grip/unplug force, retention, hot fuse/contact drop and printed attachment strength/wear remain STOPs.
The new passage also adds body/grip air communication; battery, airflow and thermal gates remain open.

Four 3 × 1 mm through-plate lacing slots are present in the carrier rails at (X,Z) = (−92,25), (−92,45),
(−34,25), (−34,45) mm. Provisionally allocate four of the existing-class 2.5 mm cable ties to separate red and black slack
loops on the cold side; the exact retention scheme may still change. Band thickness must actually measure ≤0.7 mm, and tie-head clearance must also be checked.
No tie may contact or press on the UPS PCB. Preserve qualified wire bend radii and a straight, supported fuse
section; no fold or tie load at the fuse body/leads. Fixed tied folds cannot be assumed to unfold for service.
The physical pack-disconnect reach must be proven with retention as installed, without depending on access
available only after opening a powered body. Full stored-slack, insertion and service checks remain open.

## 5. Verification status

| Evidence | State |
|---|---|
| Source and BOM consistency | CAD-free BOM validation: `python make_bom_vertical.py --check`. Independent identity/document audit: `python review_docs_audit.py`, recorded in `out/review-docs-audit.json`. Audit identity success does not turn a geometry failure into a pass. |
| Current selected main audit | 292 pass / 1 fail / 18 info, bound to the selected manifest. Actual cooler/source conflict remains at 79.902671 mm³; the intentional CSI aperture and separate skin/wall probes use corrected test context. |
| Frozen export18 main audit | Historical raw result: 288 pass / 2 fail / 18 info. Active Pi/cooler witness 79.902671 mm³; right-wall ray samples the intentional CSI opening rather than adjacent wall. Both raw failures remain visible. |
| Alternative-variant evidence | Compact Fujinon `c31096ed` and original-storage Kowa `ecb18336` have current source/file identity, valid production meshes, fresh assembly bounds, mass/CoM and core-void reports. Full alternative service/harness audits were not rerun; their old main audits remain historical, and selected compact-Kowa service results do not transfer. |
| Frozen export18 right-wall probe supplement | Historical manifest: original ray is empty at the intentional CSI slot; three actual adjacent wall locations (above, ahead, behind) each measure 2.5 mm in saved STEP. Four scoped checks pass; raw main 288/2/18 remains unchanged. This is not a global minimum-wall or strength result. See `out/compact-kowa_lm6hc/wall-probe-context.json`. |
| Assembly-envelope and structural comparison | Fresh untessellated STEP comparison and three core-void reports bind the current three manifests. Compact Kowa/Fujinon bounding volumes are about 6.8% smaller than matching baseline; original-storage Kowa is about 3.3% larger. The structural supplement updates selected compact-Kowa loads only. |
| Shadow-gap plenum geometry | Selected `shadow-plenum-checks.json` binds manifest `53e668d43847acd1f59d2b559a562476c54a23db0918debd482d632f0e8ceb77`: 49 pass / 0 fail / 21 info. Separate cold/hot/CSI external voids, exact named mouth/wall sections and no added material in the original cavity are checked. Hot sampled horizontal minimum is 299.4 mm²; no global hydraulic minimum, flow, print, strength or ingress qualification is claimed. |
| Nominal-feature dimensions / engagement constants | Report-only analytical values; not measured probes or counted verification passes |
| Panel/carrier/camera/EVF/storage/microSD service sweeps | Bounded rigid/declared-tool checks only. microSD extraction excludes the panel/switch and is panel-off only; closed-panel extraction fails against the power-switch body. Other real tools, flexible harnesses and tolerances remain unqualified. |
| Full-width HDMI, FPC and OLED ribbon sweeps | Current selected HDMI: 6 scoped passes / 0 failures. Full FPC remains unplaced, native OLED flex/whole loom and actual interfaces remain gated. |
| Selected FPS mated-carry | Current selected: 332 material checks / zero hits; nine clear keepout diagnostics reported separately. Actual roots, hand coordination, complete neighboring loom and physical fit remain open. |
| Closed-panel microSD extraction | Rejected: switch-body hits at 23 of 46 sampled poses, maximum 42.414 mm³. The selected procedure bench-fits the card before carrier insertion; panel-off or bench service only. See `out/compact-kowa_lm6hc/microsd-service-dependency.json`. |
| Rigid power pack/junction/fuse service | Current selected: 201 poses / 659 queries / zero hits. Does not qualify complete flexible wires, retention or real extraction. |
| Full power harness withdrawal and stored slack | STOP: positive 270 mm finished path includes 20 mm rigid fuse/joint zone; negative 270 mm budget includes unresolved pad-root allowance. Copper cuts/overlaps, deployment and retention remain unqualified |
| Declared CSI tool access | Source-registered port; 12 × 27 mm R1 slot, 323.14 mm². Both declared cylinders clear the selected saved solids; actual latch/jaw/FPC operation remains on HOLD. |
| USB power-head reservation | Current `shadow-plenum-head-checks.json` passes its bounded installed hard-head reservation with complete current tub coverage and accepted canonical support-source hashes. The historical missing standalone-extract attempt is retained; actual donor overmold, exit and complete EVF lead remain unmeasured/unplaced. |
| Other tool reach including power nut and screw-head engagement | Measured-tool and actual hardware confirmation pending |
| Slicer review and support/removal review | Not run |
| Coupons / measured purchased-part fit / dry assembly | Not run |
| Powered recording, warm storage, thermal, electrical and EMC checks | Not run |
| Inherited physical gates | All 56 remain open |
| M1 and revised collar load/clamp validation | Open |

No baseline computed-pass count is inherited. A renderer, mesh export, intact STEP solid or local test pass
cannot close a physical gate. A known failure in the final evidence must be reported as a failure, not folded
into “pending” or hidden behind a generic pass summary.

## 6. Candidate-specific hold points

These labels are review additions; they do not rename or retire the inherited release gates.

| Hold point | Required evidence before closure |
|---|---|
| G-V-STACK | Real board/UPS/cooler dimensions; actual standoff and thread depths; screw support/bottoming; independent carrier retention; complete +Y removal without cooler disassembly |
| G-V-STORAGE | Princeton identity/full-cap-envelope reserve, actual USB3 upper-port engagement, Linux/USB/bus-power compatibility, simultaneous USB/HDMI clearance, rear grip/removal access, availability and G-W10 warm sustained recording/write test |
| G-V-POWER | Actual 1505 drawing reconciliation, thread/nut/washer/tool fit, protected terminals, actual J2 pad map, removable connector selection/strain relief, expected boot/shutdown semantics |
| G-V-HDMI | One 3557 Pi head plus one 3556 EVF head, selected intact 300 mm ribbon, quantified usable both-unplugged tolerance reserve, keyed 10 mm developable route, physical R3 bend/thickness/clocking, exact solid/slack checks, retention/access, G-W7 and live EVF/EMI qualification |
| G-V-PIGTAIL | Real wire OD/resistance and pad coordinates; complete stored/service paths using positive 270 mm finished path (20 mm rigid fuse/joint zone included), negative 270 mm total path budget, with unresolved pad-root allowances included in both budgets and copper cuts/overlaps still to resolve through source-driven passage and 21° yaw/45° pitch XT30/fuse pose; measured tie thickness/head fit, no tie pressure/contact on UPS PCB, fixed-retention disconnect reach without assumed unfolding, bend radii and retained straight fuse section; unchanged 8.6 A/0.15 V hot-drop gate, temperatures and strain relief |
| G-V-SERVICE | Camera-before-carrier sequence; actual FPC latch/jaw/FPC occupancy through the declared 12 × 27 mm R1 slot; physical confirmation of the revised USB 5 V head/boss clearance; panel and complete stack removal with all harnesses disconnected; actual fingers/tools; all slack stored without pinching; repeated cycles |
| G-V-PRINT | Integral 1.6 mm skin/posts, nominal 6 mm gap, roof bridges and opening-edge spans; actual slicer/toolpaths, no inaccessible supports, cleanout and plenum-section coupons. Reweigh tub/panel and verify flatness, screw seats and fit after printing. |
| G-V-THERMAL | Actual cooler/fan registration, plenum pressure loss and useful flow with rear/underside/front mouth occlusion by hand, strap or a supporting surface, unsealed CSI bypass, existing separator/baffle and body/grip air communication; closed-body workload and battery-temperature tests. Inherited G-W11/G-W12 unchanged. |
| G-V-STRAP | Grip lock, shifted strap anchors and relieved rear tongue (203.5/208 mm² nominal footprint) under load; panel screws/tool reach with strap fitted; no dependence on panel for independent grip retention |
| M1 / collar | Actual lens support band, deflection, revised clamp/anchor strength and long-term creep; unchanged optical safety rules |

## 7. Review and next decision

Review the silhouette, narrowing, physical vertical stack, preserved grip and the compact-storage risk before
adopting any substitution. The original-storage variant preserves a fallback while the compact drive is tested.
Resolve the current geometry/routing failures first, then measure parts and run targeted coupons, including the new plenum section and revised mass-based joint load. Old coupon geometry remains useful only for its stated unchanged features; the old 0.90 N·m J4 load target must be checked against the new mass. Only after
source-bound CAD, full harness/tool reviews and physical gate evidence should production printing or powered
assembly be considered. Sharing this review candidate does not make it a production release recommendation.

Supporting documents: [assembly plan](ASSEMBLY-VERTICAL.md), [complete BOM](BOM-VERTICAL.md),
[baseline handoff](../HANDOFF.md), [baseline measured-parts gates](../MEASURED-PARTS.md),
[baseline wiring](../../../electronics/gs8-d2-v1/WIRING.md).

## Received-part work needed next

Use [the de-energized measurement checklist](MEASUREMENTS-TO-CLOSE.md) to resolve cooler registration, both camera-cable interfaces, actual HDMI exits, the USB donor plug/strain relief and compact SSD mating. Each row identifies the CAD hold it resolves and the required rerun. These measurements do not replace the 56 inherited physical gates or M1.
