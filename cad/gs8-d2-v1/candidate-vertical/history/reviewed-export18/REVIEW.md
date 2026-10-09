# D2 vertical Pi: review candidate

**USB source correction selected.** Export18 places the EVF power plug at the source-registered USB2 row and recording storage at USB3. The old RJ45-row pose remains a rejected diagnostic. The selected head/boss geometry is revised, but the actual donor overmold/exit and complete EVF wire route remain unmeasured/unplaced.

**CSI operational HOLD.** Export18 uses source-registered CAM/DISP 1 and a 12 × 27 mm R1 side slot (323.14 mm²). The inherited rotated connector and old tool-pass claim are superseded. Refreshed declared-tool evidence is separate from actual latch/jaw operation, cooler fit and the complete 200 mm FPC, which remain unresolved.

Status: **UNQUALIFIED REVIEW CANDIDATE, 2026-10-09. Not released, fabrication-ready or physically proven.**

This is a separate local design branch for review before any push. Baseline commit
`d38468e58eb2b02d56743e2e0cfdd8f780818a65` is preserved. Nothing in this directory authorizes procurement,
printing, publication or replacement of the baseline release. All 56 inherited physical gates and M1 remain open.

## Current checkpoint: unresolved assembly STOPs

Export18 is the selected geometry checkpoint, primary manifest
`c9e1e20710bb5f947ad47fa62328cebffb099fd3832d22909056bf8f1867cc76` (2026-10-09 07:46:39 UTC).
It retains export17's printed geometry and corrected port/control/strap layout, while replacing the defective
cached Pi fusion with 149 overlapping source-component solids. All three variant exports have matching
source/file hashes and nine/nine/ten valid one-solid printed parts. The Pi raw solid-volume sum is not its
occupied volume; source contacts are retained and non-material storage keepouts remain separate.

The detailed selected collision, routing and service audits apply to compact Kowa only. Both alternatives
have source/file identity, print-mesh and fresh assembly-bound/mass/CoM comparisons. Core-void intervals are
computed for compact Kowa and original-storage Kowa only; no separate Fujinon void calculation or complete
alternative harness/service audit is claimed. Their older `verification.json` files are historical because
they bind earlier manifests, and must not be read as current passes.

Current export18 reports show two clear declared CSI cylindrical reservations (operational HOLD), 201 rigid
power-service poses / 625 queries with zero hits, and clear static power-wire capsules versus printed solids.
The primary main report records **288 pass / 2 fail / 18 info**. One failure is the active Pi/cooler
source/proxy conflict (reported overlap witness 79.902671 mm³); actual cooler geometry and registration are
unmeasured. The other is the old right-wall probe at X−80/Z50, which now passes through the intentional CSI
opening and does not measure the adjacent wall. Preserve both raw failures rather than relabeling the report.
The selected export18 HDMI report passes six scoped checks. The FPS report has 332 clear material checks
and nine separate clear non-material reservation diagnostics. The full camera FPC and EVF feed remain unplaced.
No complete-loom, physical insertion, latch operation or service qualification is claimed.

Historical diagnostics remain available: `e8648073` had 244/0/17 main checks and 201 rigid-power poses;
its 8/4 HDMI report included four rejected over-PCB approaches. Export16 exposed the wrong USB-head/boss
and strap interference plus the 195.943 mm³ estimated-plug/source-socket conflict. These are prior
checkpoints, not current passes. The storage plug reservation is now non-material, excluded from occupied
volume/full assembly bounds; actual storage mating remains open.

Both 270 mm pigtail budgets include unresolved pad-root allowances; the positive also includes the
20 mm rigid fuse/joint zone. Neither is a copper-cut instruction. Full deployment, retained slack,
hot drop and physical battery isolation remain STOPs. The selected HDMI ribbon remains intact 300 mm;
the fragile 200 mm study is rejected. All 56 physical gates and M1 remain open.

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
| Core | Compact storage: 158 × 56 × 100 mm; original-storage alternative: 185 × 56 × 100 mm |
| Pi stack | Rigid 90° roll and relocation; real separate carrier with four stack fasteners |
| Side panel | 2.8 mm plate, inner Y25.2 and outer Y28; four accessible PH1 PT fasteners; extraction along +Y; tub bosses meet panel pads at Y23.5 without a seating gap |
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
The reported Kowa core-void intervals remain proxy-volume bounds; the approximate cooler and actual
interface/thermal gates remain open regardless of this representation repair.

## 2. Size comparison and its limits

| Main-body rectangular envelope | L × W × H, mm | Envelope, cm³ | Difference from baseline |
|---|---|---:|---:|
| Baseline D2 | 154 × 70 × 100 | 1,078.0 | Reference |
| Compact vertical candidate | 158 × 56 × 100 | 884.8 | −17.9% |
| Original-storage vertical alternative | 185 × 56 × 100 | 1,036.0 | −3.9% |

The compact core is 20% narrower and 4 mm longer than baseline. Core figures exclude lens, eyecup,
controls and grip. The following full modeled assembly bounds include individual hardware and are measured
from fresh, untessellated STEP imports bound to all three current export18 manifests. Non-material keepouts
are excluded. Dimensions are rounded to 0.1 mm; these are CAD envelopes, not measured product volumes.

| Full modeled assembly | L × W × H, mm | Bounding volume, L | Reduction versus same-lens baseline |
|---|---|---:|---:|
| Baseline Kowa | 244.8 × 79.4 × 216.8 | 4.213 | Reference |
| Compact Kowa | 248.8 × 67.2 × 216.8 | 3.624 | 14.0% |
| Baseline Fujinon | 239.2 × 79.4 × 216.8 | 4.117 | Reference |
| Compact Fujinon | 243.2 × 67.2 × 216.8 | 3.543 | 13.9% |
| Original-stick Kowa alternative | 275.8 × 67.2 × 216.8 | 4.017 | 4.6% |

The narrowed collar sets minimum Y, the exposure knob maximum Y, the eyecup minimum X/maximum Z,
and the battery cap minimum Z. Thus the compact camera is slightly longer but substantially narrower;
its complete bounding-volume reduction is about 14%, rather than the 17.9% core-only figure.
See `out/comparison/assembled-comparison.json` for source-bound unrounded results.

Core-box empty-model volume is reported separately from the exterior bounding box. The detailed candidate
Pi's full occupied-material Boolean could not be completed reliably, so its point estimates are deliberately
unset. The current method subtracts the non-Pi material union and simple PCB for the upper void bound. The
lower bound subtracts every remaining Pi source-solid's raw volume as well, conservatively including overlaps
and material outside the core. This brackets the modeled union without treating overlapping solids as
additive occupied material. Candidate intervals are rounded outward to whole cm³.

| Core-box empty-model volume | Current value, cm³ |
|---|---:|
| Baseline, original coarse Pi proxy | 741 |
| Compact Kowa, detailed Pi assembly | 588–605 |
| Original-stick Kowa, detailed Pi assembly | 706–724 |

These spaces include necessary cooling air, cable space, assembly/service clearance and omitted details.
They are not removable waste or measured unused volume. Flexible cable material and access reservations are
not fully subtracted; no complete-loom volume is claimed. The baseline retains its older coarse Pi proxy,
so differences mix packaging changes with component-representation changes. Non-material keepouts are
excluded. See `out/comparison/volume-*.json` for the report scope and manifest bindings.

The current proxy balance for compact Kowa is CoM (−45.3, 2.2, 29.0) mm versus baseline (−45.4, 0.8, 26.8) mm;
compact Fujinon is (−57.5, 2.5, 24.2) versus baseline (−56.6, 1.0, 22.0). With grip axis X−47,
the compact X offsets are +1.7 mm Kowa and −10.5 mm Fujinon. These do not justify a measured handling
or balance claim; the grip position remains a physical trial gate.

Mass caveat: the legacy XT30 row carries a 12 g lump that includes estimated pigtail mass concentrated at the
rigid proxy. Other harness masses are excluded. It is inaccurate to say that all wires are excluded, and the
actual distributed harness mass/centre of mass remains unresolved. Any current mass comparison is a planning
model with these stated limitations, not a weighed full-camera result.

The selected geometric vent provisions are four 35 × 3 mm intake slots (420 mm²), 412.5 mm² front exhaust,
96 mm² side exhaust and the separate 323.14 mm² CSI service opening. The former 11.4 mm blower-wall gap
was an illustrative-proxy value; real cooler perimeter/fan offset remain unmeasured. None establishes airflow,
pressure loss or cooling capacity. Horizontal optical and EVF bores require an explicit support and slicer
review; this tub is not described as support-free.

### Corrected rotary-switch source hold

The inherited CK1049/6.35 mm D-shaft description was inconsistent with Lorlin’s ordering table and its
Ø25 × 13 mm body proxy was undersized. The conditional corrected selection is CK1044: imperial 6.35 mm
shaft with 5.5 mm across-flat, PCB terminals, BBM, one pole, adjustable stop and 30° indexing.
Its body is Ø27.5 mm, 14.1 mm behind the mounting face, with all 13 pins reserved to 18.1 mm rearward.
The selected export18 retains the export17 centre at Z80 and uses a 24 mm knob; the scoped FPS material and selected HDMI checks are current.
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
the export18 scoped report records 332 material checks with zero hits plus nine separate clear non-material
reservation diagnostics. Its source receipt is `out/fps-service-study/fps-final-source-receipt.json`. Actual
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

The full 300 mm compact material study is frozen in
[`routing-snapshots/hdmi-compact-300-provisional`](routing-snapshots/hdmi-compact-300-provisional/manifest.json).
The selected export18 exact HDMI report records 6 scoped passes / 0 failures, bound to the current primary manifest. The historical four over-PCB
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

The export18 saved-STEP power-service report records 201 rigid pack/junction/fuse poses and 625 exact
queries with zero hits, bound to the selected primary manifest. That narrow study explicitly
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
| Selected export18 main audit | Raw result: 288 pass / 2 fail / 18 info. Active Pi/cooler witness 79.902671 mm³; right-wall ray samples the intentional CSI opening rather than adjacent wall. Both raw failures remain visible. |
| Alternative-variant evidence | Both alternatives: current export/source/file, mesh, assembly bounds and mass/CoM. Void interval applies to original-storage Kowa; no separate Fujinon void calculation. Full alternative harness/service audits are not claimed; older verification files are historical. |
| Right-wall probe supplement | Current manifest: original ray is empty at the intentional CSI slot; three actual adjacent wall locations (above, ahead, behind) each measure 2.5 mm in saved STEP. Four scoped checks pass; raw main 288/2/18 remains unchanged. This is not a global minimum-wall or strength result. See `out/compact-kowa_lm6hc/wall-probe-context.json`. |
| Exact assembly-envelope comparison | Fresh untessellated STEP comparison binds all three export18 manifests: approximately 14% compact full-bbox reduction. Kowa core-void intervals are separate conservative bounds with baseline/proxy caveats. |
| Nominal-feature dimensions / engagement constants | Report-only analytical values; not measured probes or counted verification passes |
| Panel/carrier/camera/EVF/storage/microSD service sweeps | Bounded rigid/declared-tool checks only. microSD extraction excludes the panel/switch and is panel-off only; closed-panel extraction fails against the power-switch body. Other real tools, flexible harnesses and tolerances remain unqualified. |
| Full-width HDMI, FPC and OLED ribbon sweeps | Export18 selected HDMI: 6 scoped passes / 0 failures. Full FPC remains unplaced, native OLED flex/whole loom and actual interfaces remain gated. |
| Selected FPS mated-carry | Export18: 332 material checks / zero hits; nine clear keepout diagnostics reported separately. Actual roots, hand coordination, complete neighboring loom and physical fit remain open. |
| Closed-panel microSD extraction | Rejected: switch-body hits at 23 of 46 sampled poses, maximum 42.414 mm³. The selected procedure bench-fits the card before carrier insertion; panel-off or bench service only. See `out/compact-kowa_lm6hc/microsd-service-dependency.json`. |
| Rigid power pack/junction/fuse service | Export18: 201 poses / 625 queries / zero hits. Does not qualify complete flexible wires, retention or real extraction. |
| Full power harness withdrawal and stored slack | STOP: positive 270 mm finished path includes 20 mm rigid fuse/joint zone; negative 270 mm budget includes unresolved pad-root allowance. Copper cuts/overlaps, deployment and retention remain unqualified |
| Declared CSI tool access | Source-registered port; 12 × 27 mm R1 slot, 323.14 mm². Both declared cylinders clear export18 solids; actual latch/jaw/FPC operation remains on HOLD. |
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
| G-V-PRINT | Candidate orientations, supports, minimum walls, layer load paths and tolerances; coupons and slicer evidence for every changed production part |
| G-V-THERMAL | Revised inlet/exhaust/baffle, additional body/grip air communication and vertical-board enclosure tested closed under real workload; inherited G-W11/G-W12 unchanged |
| G-V-STRAP | Grip lock, shifted strap anchors and relieved rear tongue (203.5/208 mm² nominal footprint) under load; panel screws/tool reach with strap fitted; no dependence on panel for independent grip retention |
| M1 / collar | Actual lens support band, deflection, revised clamp/anchor strength and long-term creep; unchanged optical safety rules |

## 7. Review and next decision

Review the silhouette, narrowing, physical vertical stack, preserved grip and the compact-storage risk before
adopting any substitution. The original-storage variant preserves a fallback while the compact drive is tested.
Resolve the current geometry/routing failures first, then measure parts and run targeted coupons. Only after
source-bound CAD, full harness/tool reviews and physical gate evidence should production printing or powered
assembly be considered. User review precedes any push; this candidate is not a release recommendation.

Supporting documents: [assembly plan](ASSEMBLY-VERTICAL.md), [complete BOM](BOM-VERTICAL.md),
[baseline handoff](../HANDOFF.md), [baseline measured-parts gates](../MEASURED-PARTS.md),
[baseline wiring](../../../electronics/gs8-d2-v1/WIRING.md).

## Received-part work needed next

Use [the de-energized measurement checklist](MEASUREMENTS-TO-CLOSE.md) to resolve cooler registration, both camera-cable interfaces, actual HDMI exits, the USB donor plug/strain relief and compact SSD mating. Each row identifies the CAD hold it resolves and the required rerun. These measurements do not replace the 56 inherited physical gates or M1.
