# Design-regression review: vertical-Pi candidate vs r7 (2026-10-10)

Dimension: design-regression. Reviewer: workflow agent. Read-only. Nothing in the clone was changed.

Inputs:
- Candidate: `digital8mm-vertical-nizo` at 9ced753, `cad/gs8-d2-v1/candidate-vertical/` (model.py, verify_candidate.py, REVIEW.md, ASSEMBLY-VERTICAL.md, out/compact-kowa_lm6hc/*).
- r7 release: `digital8mm` at d38468e (layout.py, checks.py, ASSEMBLY.md, HANDOFF.md r7 entry, guide/BLOCKERS-2026-10-08.md).
- Two read-only probes on the candidate's saved STEP (manifest 53e668d4), run through run_locked.py:
  `probe_driver_float.py` -> `probe_driver_float.json`, `probe2.py` -> `probe2.json` (this folder).
  The driver envelope is r7 tool 13 (layout.py:684, bit dia 6.5 x 40 + handle dia 30 x 100), applied the r7 way
  (checks.py:1405-1430: from the head bearing face outward along the screw axis) at each screw's candidate step.

## Verdict

The vertical stack is a promising packaging idea, but it is **not yet a net improvement over r7**. It trades a
released, 35-category computed audit (990 rows, 0 fail) for a narrow audit (292 pass is 55% bookkeeping) with one
real failure, and it loses or leaves unverified several r7 blocker fixes. The probes found four new physical
problems the candidate does not document: the collar centring gauge cannot be used with the camera already in
(927.75 mm3 overlap), the tab-catch tines become downward overhangs in the tub print pose, the microSD "panel-off"
path is blocked by the lens collar (the check left the collar out), and per the inherited cooler proxy part of the
fin exhaust blows straight at the camera's rear. The size gain is real in width but is mostly bought by the storage
substitution: with the same drive as r7 the vertical body is 3.3% larger by bounding volume.

Keep r7 as the release line. Treat the vertical candidate as a study until DES-1..DES-8 are closed and the r7 check
categories are ported (DES-2). Several candidate ideas are worth adopting back into r7 (see Suggestions).

## Design decisions: r7 vs candidate

| Decision | r7 | Candidate | Status | Evidence |
|---|---|---|---|---|
| Lens axis | Y0 Z60 | Y0 Z60 | Kept | model.py:43, lip cuts model.py:229-230 |
| EVF axis | Y16 Z78, F -154 | Y11 Z78, 4 mm rearward | Revised (not "preserved"); not re-checked | r7 layout.py:443; model.py:40,367 (shift (154-L, EY-16, 0)); DES-11 |
| Collar / J7-R float | body_r 30, LL (28,36), lug y_out -35 | body_r 25, LL (18,30), lug -30, s_c4 y -26.3 | Revised; nominal float gaps kept; j7_float/lens_support/lens_clamp not rerun | model.py:197-210; probe: camera-tub 0.5, adapter-tub 0.825, camera-panel 2.25, camera-collar 3.48, camera-carrier 3.91 mm |
| Tab catch (BX-4) | hood, printed roof-down | grown from integral roof, tub printed -Y down | Geometry kept; print quality and procedure lost | model.py:237-239; r7 layout.py:1162; DES-4, DES-5 |
| Hood -> integrated roof | separate hood | one-piece tub | Changed | removes hood pins (BX-6/BX-17 irrelevant); camera service now needs carrier out (DES-6) |
| Plunger -> power switch | printed plunger on Pi button | Adafruit 1505 on Pi J2 pads, 4 solder joints | Changed | REVIEW.md s4 "Power control"; switch body blocks microSD (documented) |
| Camera-before-carrier | camera after stack (step 7) | camera before carrier (step 2) | Changed | ASSEMBLY-VERTICAL.md:176-186; DES-1, DES-6, DES-12 |
| Pi carrier | horizontal stack + pi_keeper, `stack_retention` check | vertical stack on printed carrier, 2 PT screws on two 42.75 mm posts | Changed; retention unverified | model.py:168-194, 241-243; DES-3, DES-19 |
| Panel screws | concealed (s_b1/s_b2 from below, s_r1/s_r2 from the right) | 4 heads on the +Y control face | Changed | r7 layout.py:688-699; model.py:49, 426-427; DES-13 |
| Compact storage | SDCZ880 in 154 mm body | Princeton PHD-USSD-500G, 158 mm body | Changed; size gain depends on it | REVIEW.md s2, s4; DES-9 |
| Original-storage variant | (baseline) | 185 mm body, +3.3% full envelope | Larger than r7 | REVIEW.md s2 table |

## r7 design rules

| Rule | Status | Evidence |
|---|---|---|
| Straight driver at the install step | Mostly kept, not computed by the candidate | Probe: panel x4, collar s_c1..s_c4, grip lock clear tool 13 (s_c1..s_c3 bit 0.5 mm to the collar counterbore; s_c4 handle 6.5 mm to the tub; p_grip handle 1.37 mm to the strap, r7 had 2.35). Carrier PT pair fails tool 13 (DES-3). Power nut needs a "thin spanner" or deep socket, unverified (ASSEMBLY-VERTICAL.md:66-68). |
| Printed or COTS only | Kept | BOM-VERTICAL: all purchased lines are catalogue parts |
| J7-R float | Nominal pose kept; procedure and check lost | Probe gaps above; no j7_float rows; lens fitted after panel closure, no turn-back (DES-5) |
| Power last / physical isolation | Kept | ASSEMBLY-VERTICAL.md s1 and s4.8; J2 switch stated as non-isolating |
| Never weaken a check | Weakened coverage | 35 r7 categories replaced by ~9; microsd_out omits the collar (DES-2, DES-8). The pi5/cooler fail is kept visible (good). |
| Never invent measurements | Mostly kept | Unknowns are stated as holds; the cooler exhaust direction is inherited proxy (DES-7) |

## BX-1..BX-17 (r7 status lines, BLOCKERS-2026-10-08.md:81-96) in the candidate

| BX | r7 status | Candidate | Evidence |
|---|---|---|---|
| BX-1 EVF HDMI plug | Fixed: pair in unplugged, HDMI plugged up in place; `mate_paths` 13 rows | Intent kept (board from +Y, HDMI mates from -Z), new 3556 straight head. Only installed-pose head check; plug path and hand/tool corridors not recomputed | model.py:81-83; hdmi-solid-checks.json rows p_hdmi_evf, installed, premate, carried_sweep (6 rows, no mate path) |
| BX-2 QT lead | Fixed: 250 mm, panel 60 mm off, `mate_reach` | Lead kept (250 +/-10). Encoder moved (8,-7,21); reach not recomputed; 60 mm called "a starting target" | model.py:45; ASSEMBLY-VERTICAL.md s6 |
| BX-3 pigtail / XT30 at mouth | Fixed: L_cut 200 + pads-to-W, XT30 28.4 mm out, `lead_access` | Replaced: 270 mm 16 AWG, 21/45 deg junction pose, rigid service 201 poses pass; `lead_access` not rerun; G-W5 margin 7.2 mV | REVIEW.md s4 battery pigtail |
| BX-4 lens torque | Fixed: hood tab catch, `roll_catch` 59 rows, turn-back step + lint | Geometry kept on the roof; print orientation spoils contact faces (DES-4); turn-back step and visual float check lost (DES-5); `roll_catch` not rerun | model.py:237-239; probe2 tine faces |
| BX-5 knob press | Fixed: knobs at bench step 2 | Exposure knob kept at bench (B3). FPS knob now goes on after the panel, onto the nut-held switch (r7 said that case is safe) | ASSEMBLY-VERTICAL.md B3 |
| BX-6 plunger retention | Not fixed | Irrelevant: no plunger | model.py:274-275 |
| BX-7 foam pad | Fixed: pad on OLED back | Kept: foam_pad moves with the pair in `evf_in` | verify_candidate.py:109 |
| BX-8 FPC S-fold | Not fixed | Still open and wider: full 200 mm FPC unplaced; Pi end only through the 12 x 27 mm side slot | REVIEW.md s5 |
| BX-9 5 V junction tuck | Fixed: `acc_5v_tuck` corridor | Replaced by Pololu 2180/2181 inline pair (32 x 7 x 7 provisional); tuck/reach not recomputed | ASSEMBLY-VERTICAL.md s5 |
| BX-10 header housings | Fixed: 1-pin housings, `header_housings` gaps | Text kept; vertical "wall-facing" housings preconnected on bench; gaps not recomputed | ASSEMBLY-VERTICAL.md s4.4-s4.5 |
| BX-11 stack hold / pigtail U | Fixed | Irrelevant/replaced: stack enters +Y on the carrier; pigtail via swept passage and carrier lacing slots | model.py:192-193 |
| BX-12 driver margins | Not fixed (buy-check) | Partly kept: s_c4 handle 6.5 mm (same as r7); p_grip handle 1.37 mm to strap (r7 2.35); carrier counterbores fail tool 13 (DES-3) | probe_driver_float.json |
| BX-13 rest poses | Fixed: `handling` 17 rows | Not recomputed. Body narrower (63.6 mm), 864 g, CoM changed | manifest.json mass_est_g, com_est_mm |
| BX-14 shaft cut | Fixed | Kept: cut from the measured projection off the panel | ASSEMBLY-VERTICAL.md B3 |
| BX-15 gauge vs thumb | Not fixed | Still open; s_c3 moved closer to the axis (18,30); bits clear the gauge (probe). But see DES-1: the gauge cannot be used at the candidate's step | model.py:207-208 |
| BX-16 run lead window | Fixed: window 3.5 >= 3.2 | Floor hole and base opening changed; window not recomputed | model.py:31-33 |
| BX-17 hood pins | Not fixed | Irrelevant: no hood | ASSEMBLY-VERTICAL.md s2 |
| C-16 service order | hood needs collar off | Irrelevant; replaced by "camera and collar refit need carrier out" (DES-6) | |

## Findings

| id | sev | kind | title | evidence | failure scenario | fix | closable |
|---|---|---|---|---|---|---|---|
| DES-1 | major | latent | Step 2 fits the collar with the gauge after the camera; the gauge overlaps the installed C-CS adapter | ASSEMBLY-VERTICAL.md:176-186 (camera, then "Fit and centre the lens collar with the printed gauge"); probe: centring_gauge.step vs c_cs_adapter 927.75 mm3. r7 ASSEMBLY.md:206 "Lens collar first, camera still out". | The builder cannot seat the gauge; the collar is tightened uncentred (r6 X2: 0.60 mm worst vs 0.75-0.825 float gaps), so the adapter can touch the lip. Every later collar refit needs the camera out, which needs the carrier out. | Reorder: collar + gauge + s_c1..s_c3, gauge out, then camera (the camera_in check already assumes the collar is present, verify_candidate.py:108). Add a check that gauge and camera never coexist. State in service that a collar refit needs camera and carrier out, or design a gauge that does not enter the lip. | docs |
| DES-2 | major | latent | r7 rule checks were dropped; the 292-pass count is not comparable | verification.json: integrity 45 + roundtrip 45 + source_binding 71 = 161 of 292 passes are bookkeeping; 108 pairwise interference, 10 motions, 13 probes. r7 checks.json has 35 categories incl. driver 11, service_driver 11, j7_float 50, roll_catch 59, lens_support 42, lens_clamp 6, mate_paths 13, mate_reach 6, header_housings 10, lead_access 9, handling 17, evf_restraint 8, stack_retention 1, print_overhang 13. None runs on the candidate. | A rule break (driver, float, catch, reach) goes unseen. DES-1, DES-3, DES-4, DES-8 were found only by hand probes. | Port the r7 categories to the candidate geometry (or run checks.py on a candidate layout) before comparing pass counts. Report per-category coverage next to the summary. | checks |
| DES-3 | minor | latent | Carrier PT counterbores are dia 6.4, narrower than the r7 tool-13 bit (6.5) | model.py:191 `cyl('y',3.2,...)`; probe2: bit 6.5 overlaps carrier 2.432 mm3 (p_carrier1, Y19.8..22.2) and 0.405 mm3 (p_carrier2); 6.0 clears. r7 PT counterbores are dia 7.0 (layout.py:690-699). | The specified power bit (turned shank <= 6.5 over the first 8 mm, BX-12) cannot reach the head; the builder uses a thinner or angled tool. | Open the two counterbores to dia 7.0, or specify and check a dia <= 6.0 bit. Port the r7 driver check. | cad |
| DES-4 | major | latent | Tab-catch tines become downward overhangs in the tub print pose; the +Y catch face needs supports | Tines from L.tab_catch_boxes() extended to Z98 (model.py:237-239); tub prints -Y face down (manifest print_poses tub face_down -Y). probe2: -Y-normal faces at Y8.28 (the +Y tine's catch face, 57.64 + 11.02 mm2, X-14.5..-8.2, Z78.5..97.5) and Y-11.28/-20.28. r7 printed the hood roof-down (layout.py:1162 face_down '+Z'), so tines rose clean from the bed. No print_overhang check in the candidate. | Support in the 16.6 mm tab slot scars both catch faces; the roll window (r7 0.679 / 0.129 mm, first contact 3.25 deg) is lost or the tab binds, so the camera touches a printed tine in the final pose. | Redesign the catch to print clean in -Y-down (e.g. a separate printed catch block that slides in from +Y and is clamped by the panel, printed upright, no screw), or post-finish to a gauge. Add print_overhang and roll_catch to the candidate audit; add a tine coupon to G-V-PRINT. | cad |
| DES-5 | major | latent | Lens is fitted after the panel closes; r7's float procedure (push, turn back, look) is lost | ASSEMBLY-VERTICAL.md s6 (panel) precedes s7 (lens, :278-279 "Verify the metal-tab catch and inherited floating-camera seating method"); grep finds no "turn back"/"tine" text. r7 ASSEMBLY.md:222 (panel off; fingertip push; turn to the other tine and back half way; "touches neither the tub lip, the counterbore nor the tab-catch tines"; then s_c4). | s_c4 is snugged with the tab still loaded on a tine, or the camera off its seat, and nobody can see it through a closed panel. J7-R float is broken for the life of the build. | Fit the lens and s_c4 with the panel off, right after the camera (before EVF and carrier), and copy the r7 step 8 text incl. turn-back and the visual float check; add the r7 lens_turn_back lint to the candidate docs. | docs |
| DES-6 | major | latent | Camera, camera FPC and collar refit service now require removing the whole Pi/UPS/cooler carrier | ASSEMBLY-VERTICAL.md service row "Camera / adapter": "Remove panel and complete carrier first where the reviewed clearance requires it"; camera installed before carrier (REVIEW.md s1 table); carrier removal row carries six STOPs (FPC release, pigtail withdrawal, run lead...). r7: camera in at step 7 after the stack; removal did not need the stack out. | A lens-swap mishap, FPC change or collar refit turns into a full electronics teardown with the riskiest STOPs, many times more connector cycles (Molex J2: 30 cycles). | Make the trade explicit in REVIEW (service matrix: r7 vs candidate per item). Consider a camera exit path that does not cross the carrier (e.g. stack shifted rearward, camera out +Y ahead of the carrier front at X-29). | user_decision |
| DES-7 | major | latent | Per the inherited cooler proxy, part of the fin exhaust blows straight at the camera's rear | Fin channels run along +X and end at X-37.5 (r7 COTS cooler x1 -9.5, blower x -72.8..-42.8, shifted -28); after the roll the exhaust face spans Z14.75..55.25, Y-8.3..-1.2. Camera rear X-25.1, Z40.2..82.1 (manifest). Overlap Z40.2..55.25 = 37% of the exhaust face, 12.4 mm away. Hot wall slots only at Z16..40 (vent_geometry.py:12,15). r7 exhausted at Z20.2..36.3, under the camera (bottom Z40.75), straight into out_wall X-19..-5 Z21..37. | Warm air heats the GS sensor/PCB (noise, drift) and the FPC; the measured "cooling" may look fine at the Pi while image quality degrades. Not in G-V-THERMAL. | Add the real cooler's exhaust direction to MEASUREMENTS-TO-CLOSE; if confirmed, add a deflector to the carrier that turns the plume to -Y into the hot slots, and log camera temperature in the thermal tests. | measurement |
| DES-8 | major | latent | microSD +X path is blocked by the lens collar; the checked path leaves the collar out; the front slit has no use | verify_candidate.py:112 microsd_out fixed set = tub, gs_camera, c_cs_adapter (no lens_collar). probe2: the card meets the collar at dx 32 (X0.3), worst 75.55 mm3; power_button at dx 5 (42.41 mm3, documented). Slit cut model.py:273. r7 SD_SLOT at Z15.9..18.6 sat below the collar (layout.py:542). | REVIEW's "panel-off" microSD service is not possible along the checked path; a card swap means carrier removal or collar + lens removal (and then DES-1). The slit is an extra hole in the front face. | Add lens_collar and lens to microsd_out; either check a dog-leg path (+X ~10 mm, then +Y) with the panel off, or state carrier-out service and delete the slit. | checks |
| DES-9 | minor | latent | Size gain comes from the storage swap and is cut by the concealed-vent skin | REVIEW.md s2: same drive (original storage) full envelope 4.352 L vs r7 4.213 L = +3.3%, core 1,176.6 vs 1,078 cm3 = +9.1%. Compact -6.8% needs the Princeton SSD (Linux absent from vendor OS list; G-W10 open). Skin adds 7.6 mm: export18 56 mm -> 63.6 mm, so the plenum uses 54% of the 14 mm width gain (70 -> 56). | The headline -6.8% is read as a property of the vertical stack. If the Princeton SSD fails G-W10 or Linux, the vertical body is larger than r7. | State the same-drive comparison and the plenum width cost next to the headline. Test the SSD on the Pi first. | docs |
| DES-10 | minor | latent | No mapping from r7 gates and BX fixes to the candidate | Candidate docs never cite BX-1..BX-17 or r7 gates G-EVF-3, G-QT-1, G-HDR-1, G-CAM-1/2, G-ENC-1 (grep); "all 56 inherited gates remain open" although G-SNAP-1/2 (hood), G-PLG-1 (plunger), G-KEEP-1 (pi keeper) refer to deleted parts. | A reviewer cannot tell which r7 fixes still hold; dead gates stay "open" and live ones lose scope. | Add a gate and BX table: retired / carried / re-scoped / replaced by G-V-*. The BX table above is a start. | docs |
| DES-11 | minor | latent | EVF axis moved 5 mm inboard and 4 mm rearward but is listed under "preserved / revised" without the r7 value | r7 layout.py:443 barrel at Y16 Z78, F-154; model.py:40 EY=11, :367 shift (154-L, EY-16, 0); REVIEW.md s1 table row "EVF axis". evf_restraint (8 rows) not rerun. | Eye/nose clearance at the rear face and the EVF board stop are not rechecked. | Give r7 and candidate values; port evf_restraint; check face clearance for left- and right-eye users. | checks |
| DES-12 | minor | latent | Camera sits unretained rearward from step 2 until the panel's rear catch arrives at step 6 | The rear catch is on the panel (model.py:292-293). camera_in enters with an 11.1 mm rearward offset (verify_candidate.py:108), so before the carrier it can slide back that far; probe2: with the carrier present the camera meets the carrier after 4.0 mm (5.45 mm3). r7 had the lens on at the next step (ASSEMBLY.md:206-222). | During EVF, carrier insertion and wiring the camera slides off its lip or rests on the printed carrier, scraping the FPC or the adapter. | Fit the lens and s_c4 in step 2 (also closes DES-5) or specify a temporary retainer and a body orientation for steps 2-5. | docs |
| DES-13 | info | latent | Panel fixings moved from hidden to four visible heads on the control face | r7 s_b1/s_b2 from below and s_r1/s_r2 from the right (layout.py:688-699); candidate four PH1 heads on the +Y face (model.py:49, 426-427). | Conflicts with the stated "Braun Nizo simplicity" look; but service gets simpler (one side). | User choice; if hidden heads matter, add printed press-in caps (no new fastener). | user_decision |
| DES-14 | major | existing | Pi/cooler source-proxy overlap 79.902671 mm3 is still a failure | verification.json FAIL pi5/cooler 79.902671 mm3 (the only fail); REVIEW.md s5 | The real cooler may not seat on the rolled stack, or contacts components; thermal contact unknown. | Measure the real cooler (MEASUREMENTS-TO-CLOSE) and rerun; do not reclassify. | measurement |
| DES-15 | major | existing | Print holds: front mouth needs ~35 mm bridging; plenum roof, posts and cleanout unproven | README.md "Print hold"; REVIEW.md s2 concealed passages; CHECKPOINT-STATUS prominent_holds. Slicer not run. | Sagged roof or trapped support in the plenum; the largest part (158 x 105 x 63.6 mm footprint) is scrapped. | Slice and print the two plenum coupons and a tine coupon before any tub. | measurement |
| DES-16 | major | existing | Thermal path unproven; the concealed plenum adds loss and occlusion risk | REVIEW.md s2: hot sampled minimum 299.4 mm2 < 510 mm2 wall slots; blocked underside leaves 210 mm2 front; CSI slot is an unsealed bypass; no sealed duct. r7 vents fed the cooler more directly (inlet_roof over the fan, out_wall beside the fins). | Throttling during warm recording; dropped frames (G-W10/G-W11/G-W12). | Closed-body thermal test with hand/strap occlusion cases before adopting the plenum; compare with a simple-slot body. | measurement |
| DES-17 | minor | existing | Longer 270 mm pigtail leaves only 7.2 mV of the 0.15 V G-W5 budget | REVIEW.md s4: 0.142811 V wire-hot vs 0.15 V; r7 cut 200 mm + pads-to-W with a stop rule at 25 mm (HANDOFF.md r7 BX-3). | Hot fuse/contact/pad resistance exceeds the budget and the build fails G-W5 after wiring. | Measure PRC wire and pads early; consider 14 AWG or a shorter path; keep the ceiling. | measurement |
| DES-18 | minor | existing | Power switch needs solder on Pi J2 pads, an unverified nut and a 30-cycle connector | REVIEW.md s4 Power control: J2 position a hypothesis, nut reserve unverified, Molex 30 mating cycles; ASSEMBLY-VERTICAL.md:66-68 thin spanner. | Pad damage on the Pi; connector wears out under panel service; nut cannot be driven straight. | Inspect the real J2 pads and 1505 hardware; choose a higher-cycle connector; confirm a deep-socket (straight) drive for the nut. | measurement |
| DES-19 | minor | existing | Stack retention rests on two diagonal PT screws into two 42.75 mm posts; r7 keeper/stack_retention check gone | model.py:241-243 (posts Y-25.55..17.2), CARRIER_SCREWS model.py:48; G-V-STACK "independent carrier retention". | Drop/shock rocks the carrier about the diagonal; pogo contact to the X1203 is disturbed. | Port stack_retention; add a third locating feature (printed tongue/slot) without a new screw. | checks |
| DES-20 | minor | existing | Compact body depends on an unproven SSD | REVIEW.md s4 Recording storage: Linux not in Princeton's list; G-W10 >= 100 MB/s warm sustained open; G-V-STORAGE. | SSD fails on Pi/Linux or throttles; only the larger 185 mm body remains. | Bench the SSD on a Pi 5 first. | measurement |
| DES-21 | major | existing | Camera FPC route unplaced; Pi CSI latch reachable only through a visible 12 x 27 mm side slot | REVIEW.md s5 (full FPC unplaced; CSI on HOLD); model.py:263; ASSEMBLY-VERTICAL.md s5 STOP. | The FPC cannot be latched or stowed; the slot is a permanent ingress/thermal bypass on the concealed face. | Place the full 200 mm FPC; bench-test the latch through the slot; consider a press-in printed plug for the slot. | cad |

## Overall judgement

Gains (real): body 9% narrower (63.6 vs 70 mm); 9 printed parts vs 12; no hood pins or plunger (BX-6, BX-17
gone); all panel screws from one side; source-registered Pi ports, corrected CK1044 switch source and Pi model
representation (useful to r7 too); broadside vents hidden.

Losses and new risks: same-drive envelope +3.3%; length +4 mm; the plenum eats over half the width gain; one known
failure (DES-14); exhaust toward the camera (DES-7); camera, collar and microSD service now go through carrier
removal (DES-1, DES-6, DES-8); tab catch print quality (DES-4) and float procedure (DES-5) regressed; verification
coverage dropped from 35 categories to about 9 (DES-2); print holds on the largest part (DES-15).

Net: not an improvement yet. It could become one if the plenum proves thermally and DES-1..DES-8 are fixed.

## Suggestions the user could adopt

1. Port r7 checks.py categories (driver, service_driver, j7_float, roll_catch, lens_support, lens_clamp, mate_paths,
   mate_reach, header_housings, lead_access, handling, evf_restraint, stack_retention, print_overhang) to the
   candidate before any pass-count comparison.
2. Rewrite step 2 as: collar + gauge + s_c1..s_c3 -> gauge out -> camera -> lens + r7 turn-back + s_c4, all
   before EVF and carrier (closes DES-1, DES-5, DES-12).
3. Make the tab catch a separate, upright-printed block that slides in from +Y and is held by the panel (no screw).
4. Measure the real cooler's exhaust; if it is +X, add a carrier-mounted deflector to the hot slots.
5. Open the carrier counterbores to dia 7.0.
6. Fix the microSD path check (add collar and lens) and either check a dog-leg or delete the front slit.
7. Decide the vent concept by test: plenum (63.6 mm) vs export18-width body (56 mm) with small discreet slots.
8. Bring the useful corrections back to r7: CK1044 source correction, source-registered Pi ports, USB head
   correction and the Princeton SSD trial (as an r7 storage option).
9. Add an r7-vs-candidate service matrix (camera, collar, microSD, EVF, panel, stack, grip) with step counts and
   connector cycles.
