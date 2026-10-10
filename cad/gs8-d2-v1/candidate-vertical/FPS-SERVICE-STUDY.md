# FPS service study

This is an engineering study, not a print or assembly release. The selected service concept keeps the complete FPS harness and genuine inline connector mated while the switch and Pi/carrier move outward together. The Pi HDMI head stays mated; the EVF HDMI end is disconnected. The connector can be separated on the bench. There is no in-body flange-grasp, deployment loop or cut-tie step in the selected sequence.

## Selected source and geometry

- Switch: Lorlin CK1044, imperial PCB, break-before-make, one pole, adjustable two-stop setting. The official [CK drawing](https://lorlinelectronics.co.uk/wp-content/uploads/2020/11/CK-ROTARY-Nov-2020-1.pdf) replaces the inherited CK1049/6.35D mismatch. The source body is Ø27.5 × 14.1 mm. It is centred at X−111/Z80 with mounting face Y25.2, body rear Y11.1 and provisional pin tips Y7.1. All 13 pin reservations are retained; only A and throw 2 are wired. Actual terminal section, view/clocking and molded numbering require receipt checks.
- Controls: position 1 is open/high = 18 fps; position 2 closes A to throw 2, low = 24 fps. The two detents are 30° apart. Shaft trim, stop washer, supplied nut/washer, mounting torque and the D-bore coupon are separate gates. The nut’s inherited 12.7 mm AF reservation is not a published Lorlin dimension.
- Inline pair: Molex 2181110202 male 225 ± 6 mm assembly and 2181120201 female 150 ± 6 mm assembly. Both have black 28 AWG UL1061 leads and blunt free ends. This is a genuine 51047/51021 wire-to-wire pair; the generic PH inline proxy is superseded.
- The full mated length is 9 mm reference, not a guaranteed maximum. The male housing is 8 mm long; the female is 3.95 mm long. The female’s exposed flange is small, so a successful generic half-body finger pinch has not been claimed. Bench separation still requires actual grip and stroke verification.
- Selected route: `fps_ck1044_mated_carry.py`, unchanged X−103.5 and X−114.5 rear-wall vertical main legs, fixed delayed S bend at Y5…8.464, outer turn Y23.7, R5.2 mm paired envelope and R3.2 mm terminal branches. The corrected carrier leaves approximately 0.2 mm nominal local clearance at the outer turn. That is a tolerance gate.
- Central switch rest: `fps_fixed_support.py`, with the widened version also isolated in `fps_fixed_support_central_wide.py`. The selected contact-pad extension to Y13…24.5 is now adopted in the canonical helper, byte-identical to the separately tested `fps_fixed_support_pad_proposal.py`. It is an assembly rest, not a handle or reaction fixture for unplugging.
- Open connector guide: `fps_pair_guide.py`. It retains the housing in X/Z, remains open in both axial directions, and has a 2.8 mm throat flaring to 4.6 mm so the narrower curved wire can leave upward as the complete group slides +Y. No disposable tie is selected.

## Intended sequence

Removal (service route `panel`, then `module`, in [`steps.py`](steps.py); the generated routes are in
[ASSEMBLY-VERTICAL.md section 5](ASSEMBLY-VERTICAL.md#5-service-routes)):

1. Shut down, isolate the battery (`safety` route) and release the other required panel connections according to their own verified service instructions.
2. Remove the FPS knob (`svc_knob_fps_off`), then the mounting nut with a deep socket on the bushing axis (`svc_fps_nut_off`, straight-driver rule, VN-46) while supporting the switch, then the mounting washer (`svc_fps_washer_off`), preserving the two-position stop setting. Measure the actual nut and choose the matching deep socket; the proxy does not establish its across-flats.
3. Remove the four panel screws. Give the shaft tip gentle axial support while sliding the panel +Y8.5 mm. At that nominal position the panel inner face is Y33.7, beyond the Y33.2 bushing end. The outer face is Y36.5, leaving only 0.5 mm of shaft tip; this does not establish a pinch grip. Transfer support to the accessible bushing as the panel clears, then finish removing the panel and part QT and J2 by their housings. Actual fingertip shape, friction, sag and panel tilt remain physical checks.
4. Disconnect the EVF HDMI end. Keep the Pi HDMI head mated; its in-body unplugging has a separate known power-wire conflict. Release the other fixed-to-carried connections and carrier screws under their own instructions.
5. Support the exposed switch bushing with one hand and the carrier with the other. Translate the switch, complete mated FPS harness, Pi/carrier and full Pi-mated HDMI together +Y. The group must preserve its checked relative arrangement. The rest and pair guide remain attached to the tub.
6. Set the group on a supported bench. Separate the PicoBlade pair there only if needed, holding the housings and pulling along their mating axis. Never pull on the wires.

Refit (build order, ASSEMBLY-VERTICAL.md section 4; review VN-40): the switch and its mated pair are part of the module (B2) and ride in with the carrier, hand-supported (step 4). The panel subassembly carries no FPS hardware (B3). In step 6 the panel goes on along −Y, guiding the bushing and its locating peg into the panel hole and slot while the other hand supports the switch body (`panel_in`); the four panel screws are driven before the FPS knob is on (`panel_screws`); then the mounting washer (`fps_washer_on`), the nut with the deep socket on the bushing axis and an anti-rotation check (`fps_nut_on`), and last the knob on the two paper strips, backed by the nut on the panel (`knob_fps_on`). Every removal above names its refit in `steps.SERVICE` (`reverse_of`).

This is a modeled sequence with a coordinated-hand trial still required. It does not certify all other panel leads, the camera FPC, a real hand’s motion, connector friction or the printed supports’ strength.

## Wire and termination accounting

The purchased 225 + 150 = 375 mm figure is the sum of two assembly-axis stock lengths. It is not the installed harness length or total copper length. The factory wire-length datum is the rear housing wire-exit face to the blunt free end, excluding the housing. Minimum free stock is 219 mm male and 144 mm female, before any trimming or termination deductions.

| Segment | Modeled axis length | Termination notes |
|---|---:|---|
| Pi side, GPIO exit to mated male exit | 200.000 mm per nominal conductor axis | Includes retained GPIO donor stubs and the splice region; does not use 200 mm of factory male wire alone |
| Female exit to A pin-tip datum | 95.4644 mm | Shared 80 mm bundle envelope plus individual terminal branch |
| Female exit to throw 2 pin-tip datum | 102.4759 mm | Shared 80 mm bundle envelope plus individual terminal branch |

The modeled conductor-axis sum is 597.9403 mm for the two Pi-side axes plus the two switch-side axes. This is not an exact copper-cut schedule: the shared bundle, GPIO fanout, internal crimp/contact lengths and actual solder lap are not measured conductor centre-lines.

Use two differently identified Adafruit 1950 female/female donor leads from the 20-wire pack, retain one genuine 2.54 mm female head from each and splice to the blunt male-assembly leads. Two added solder joints and two sleeves are required; this raises the complete candidate joint tally from 22 to 24. Keep the remaining 18 intact donor leads and the removed ends/offcuts as workshop stock. The factory Molex housing is retained on each assembly; none is discarded.

The two maximum finished splice reservations are Ø3 × 10 mm at X−103.5/Y−23.4, Z41…51 and Z55…65. Their nominal path midpoints are 58.253 and 72.253 mm from the GPIO proxy exit. For an illustrative 3 mm overlap, cuts would extend 1.5 mm past each midpoint: donor free tails about 59.753/73.753 mm, male free tails about 143.247/129.247 mm. These are planning dimensions, not a shop cut instruction. Confirm the actual GPIO exit, individual-core path and a solder/heatshrink coupon before cutting. A provisional 3 mm switch-terminal allowance gives about 98.464/105.476 mm, within the 144 mm minimum female stock; the actual lap/strip specification remains open.

The older estimates that added a full 3 mm on both sides of a splice over-reserved the overlap and are superseded by the midpoint convention above. Earlier 225 mm installed-main deployment accounting is also superseded.

Identify both black conductors with durable FPS labels and continuity tests from the molded connector cavity numbers to GPIO13/pin33 and GND/pin34, then to the intended A/2 switch contacts. Do not infer polarity from color. If the same family is used for J2, distinct FPS/PWR labels and physical placement are required because polarization does not prevent cross-connection. The verified W/W rating for these 28 AWG tin contacts is 1.5 A/125 V and 30 mating cycles; the selected use is low-current signaling.

## Evidence and limits

The final scoped FPS result uses export18, manifest SHA256 `c9e1e20710bb5f947ad47fa62328cebffb099fd3832d22909056bf8f1867cc76`, built 2026-10-09 07:46:39 UTC. All nine printed parts are valid one-solid. The integrated FPS audit passes eight static full-wire/pair/splice checks and 36 carried poses of nine complete FPS/switch pieces (+Y0…70 mm, 2 mm steps): 332 material checks, zero hits. Nine separate checks against the explicitly non-material storage-plug reservation also have zero overlap. The reservation's STEP remains hash-bound and is not counted as occupied material. Every mechanical source, STEP, frozen wire input and imported sweep helper stayed unchanged through verification.

The related export18 selected-HDMI audit passes all six checks, including the corrected USB head, both complete 300 mm ribbon poses and the selected carried sweep. Export16's 283.8663 mm³ USB-head/lower-boss failure is preserved as history; the revised boss clears in export18. The corrected USB2 head still has no measured wire exit or accepted full 5V soft return, and the corrected CSI/FPC remains independently gated. These scoped results do not establish a whole-loom or physical assembly release. Canonical source adoption, earlier failed results and the final report hashes are recorded in `out/fps-service-study/fps-final-source-receipt.json`.

- `out/fps-service-study/integrated-fps-export18-checks.json`: final scoped FPS result, 332 material checks and nine separate non-material reservation diagnostics, all clear. Includes unchanged manifest/source/STEP/input/helper bindings.
- `out/fps-service-study/integrated-fps-export16-checks.json`: preserved earlier scoped FPS pass; its separate USB-head/service audit failed before the boss correction.
- `out/fps-service-study/fixed-fps-service-checks.json`: corrected static switch/wires/splice reservations; shaft/panel staging; original rigid removal checks. No complete-wire removal claim follows from the rigid switch result alone.
- `out/fps-service-study/mated-carry-checks.json`: 36 complete mated-harness/switch poses. Three late main-wire/rest hits exposed the superseded right-side rest; all other fixed-solid checks passed.
- `out/fps-service-study/central-rest-checks.json`: narrow central rest, all static checks and 71 complete carried poses, zero hits. The widened rest has its own report.
- `out/fps-service-study/central-rest-wide-checks.json`: selected 6.8 mm rest: zero static, wire, bushing-fingertip and 71-pose carried hits. The combined tub/rest/guide is valid one-solid.
- `out/fps-service-study/central-rest-pad-checks.json`: the 4.0035 mm³ rearward pad addition clears the same static/71-pose set. Full rest volume is 1297.6740 mm³, valid one-solid; root overlap remains 90.78 mm³.
- `out/fps-service-study/open-guide-checks.json`: valid one-solid guide; 71 complete carried poses, zero hits. The source body profile and actual print retention still require physical checks.
- `out/fps-service-study/central-rest-hdmi-bounds.json`: the entire narrow central-rest box is disjoint in XZ from every full-material HDMI cell in all three saved shapes, which proves its clearance for any +Y translation. `selected-support-hdmi-bounds.json` refreshes this for the widened rest and open pair guide, with zero XZ candidates for all three complete ribbon shapes.
- `routing-snapshots/hdmi-ck1044-clear-20261009-0524/fps-mated-carry-context-checks.json`: exact full mated FPS shapes clear all three corrected HDMI material poses. Co-translation preserves that relative geometry.

The selected-STEP structural screen is saved in `structural-review/actual-shelf-screening.json`. With an assumed 12 g switch and E = 1.6 GPa, it predicts 0.169 mm vertical bending plus a 0.0025 mm torsion surrogate at gravity. A separate 0.5 N harness force gives about 0.729 mm combined motion. The 5g sensitivity gives about 0.858 mm and 3.56 MPa nominal bending stress. This is an asymmetric variable-section beam screen, not FEA or a load rating; actual print stiffness, wall compliance, body contact and harness preload remain unmeasured. Hand support throughout service remains required.

No terminal/body overlap has been waived as solder contact. Flexible wire ends meet the provisional terminal-tip planes; actual lugs, solder/heatshrink volumes, the two-conductor GPIO transition and cable-exit strain relief are explicit unqualified regions. The sleeve reservations bound a proposed finished envelope but do not certify a solder joint.

## Rejected and superseded studies retained

The original 21-pose PH study hit the carrier and had a diagonal switch-root overlap. The S bend and normal tail removed those modeled hits but did not establish a genuine connector or access. The angled long-jaw tool had a clear final pose but struck the tub during insertion. The moving-panel long-loop, high-Z slack loop and rearward EVF-intersecting saddle proposals failed. The right-side switch rest obstructed late complete-wire extraction. The X−82.91 replacement main riser hit QT and would compromise the newly identified CSI corridor, so it is rejected. Their sources, full shapes and reports remain in `routing-snapshots` and `out/fps-service-study`.

## Source drawings

- [Male assembly, including 2181110202 table](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/218/218111/2181110201_sd.pdf)
- [Female assembly 2181120201](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/218/218112/2181120201_sd.pdf)
- [51047 male housing and mated reference envelope](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/510/51047/510470200_sd.pdf)
- [51021 female housing, revision C](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/510/51021/510210200_sd.pdf)
- [Wire-to-wire product specification](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/productspecificationpdf/510/51021/510211009-PS-000.pdf)
- [Application specification](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/applicationspecificationspdf/510/51021/510210001-AS-000.pdf)
- [Adafruit 1950 donor leads](https://www.adafruit.com/product/1950)
