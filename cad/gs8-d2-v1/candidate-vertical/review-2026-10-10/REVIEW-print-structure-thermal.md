# Review: print, structure and thermal (dimension `print-structure-thermal`)

Target: `digital8mm-vertical-nizo` at 9ced753, `cad/gs8-d2-v1/candidate-vertical`, selected manifest `53e668d4...` (compact Kowa).
Reviewer: workflow agent, 2026-10-10. Read-only. The committed snapshot was not modified.

## Method

- Re-applied r7's own computed print check (`checks.check_print_overhang`, imported read-only from the snapshot) to the candidate's committed print-pose STLs (`out/compact-kowa_lm6hc/stl/*.stl`, poses from `manifest.json`). r7 rule: layer 0.2, 45 deg, cantilever 1.0 mm, bridge 30 mm, 8 directions, px 0.1, no declared support zones. Output `overhang_b30.json`.
- Single-raster-direction analysis of the tub's first plenum-roof layer (print z 7.6, model y -28). A slicer prints one bridge direction per region, so the per-pixel best-of-8 r7 metric is optimistic. Output `roof.json`.
- Region mapping back to model coordinates (`probe_map.py`), a 2D morphological thin-feature screen (`probe_thin.py`) and camera-to-printed-part minimum gaps. See the probe status note at the end.
- CAD-free recomputation of the structural supplement (`update_concealed_vent_structure.py` inputs), the collar anchor statics (r7 `check_lens_clamp` formula) and an orifice-network comparison for the CSI slot.
- Probe scripts and outputs: this directory (`probe_overhang.py`, `probe_roof.py`, `probe_map.py`, `probe_thin.py`, `*.json`, `*.log`).

Coordinates: model frame unless marked "print". Tub print pose: print X = x+158, print Y = 100-z, print Z = y+35.6.

## Verified claims (no finding)

- Structural supplement arithmetic reproduces exactly from its inputs: upper mass 673.15 g, 5 g floor moment 1803.05 N mm, grip moment 4644.86 N mm, equal-share J4 screen (1803.05+58.84)/2000 = 0.9309 N m, rounded 0.95 N m, 70 % case 1.3033 N m (`structural-review/concealed-vent-structural.json`).
- Tub proxy mass 154.59 g = 169 977 mm3 (plenum report `tub_valid_single_solid`) x 1.07 x 0.85.
- Front-mouth hold geometry is as documented: `vent_geometry.py:20` cuts the front frame over Z5..40; the last post column is x -14 (edge -13.2), 10.7 mm from the frame face at x -2.5; the two-ended span along Z is 35 mm.
- Revised collar anchor polygon still meets r7's 10 mm rule (my recomputation 14.43 mm; r7 16.01 mm).

## Findings

| ID | Sev | Kind | Title | Closable by |
|---|---|---|---|---|
| PRI-1 | major | latent | r7 print_overhang (and thin_wall / critical_features) gate dropped; re-applied, 4 of 10 parts fail | checks |
| PRI-2 | blocker | latent | Plenum roof is not post-supported: best single raster direction still needs 44-47 mm bridges | cad |
| PRI-3 | major | existing (understated) | Rear and both underside mouths repeat the front-mouth hold, and are larger (70 / 71 / 54 mm) | cad |
| PRI-4 | major | latent | Carrier print pose floats the whole frame 2 mm above the bed (1963 mm2 unsupported) | cad |
| PRI-5 | minor | latent | Grip regression: new power-passage pocket roof unsupported next to the J4 rear tongue | cad |
| PRI-6 | minor | latent | Collar LR compression foot overhangs the reduced R25 body | cad |
| PRI-7 | major | latent | Revised collar not re-run through r7 lens_clamp / inserts / j7_float; washer now tangent to bit relief | checks |
| PRI-8 | major | latent | Structural base values are unreproducible; a 2.25x higher J4 lip model is in the same JSON but unreported | repo |
| PRI-9 | major | latent | 0.95 N m J4 screen does not bound the original-storage fallback (about 0.976 N m) | checks |
| PRI-10 | major | latent | CSI slot conductance is comparable to the whole concealed cold path; it is likely a main intake | cad |
| PRI-11 | minor | latent | Front hot mouth plume rises over the collar clamp lug (M1 creep interaction) | measurement |
| PRI-12 | minor | existing (understated) | Hand/strap occlusion is the normal-use case: both underside mouths sit on the strap side | measurement |
| PRI-13 | minor | existing (quantified) | Closed-plenum cleanout/inspection reach is 83-97 mm through a 6 mm post forest | cad |
| PRI-14 | minor | latent | Integral skin bed-face edges have no r7 bed chamfer | cad |
| PRI-15 | info | latent | Plenum pressure loss can be bounded by computation now; it is not only a physical gate | checks |
| PRI-16 | info | latent | Fujinon variant CoM 11.2 mm behind the grip axis; supplement covers compact Kowa only | docs |

## Finding details

### PRI-1 (major, latent) r7 print gate dropped; re-applied it fails
Evidence. r7 `out/checks.json` has `print_overhang` 13/13 pass (tub with 4 declared zones), `thin_wall` 12/12, `critical_features` 131 pass. The candidate main audit (`out/compact-kowa_lm6hc/verification.json`, 292/1/18) only has categories integrity 45, interference 118, motion 10, roundtrip 45, source_binding 71, step probes 13, nominal 7, physical 1. No candidate file calls `check_print_overhang` (grep). `print-mesh-checks.json` checks watertightness and bed fit only. Re-applying r7's rule to the committed STLs (`overhang_b30.json`): tub FAIL (12 unsupported regions; largest 665.9 and 417.9 mm2 at print z 7.6), carrier FAIL (1963.1 mm2 at print z 2.0), base_grip FAIL (102.9 mm2 at print z 5.4), lens_collar FAIL (11.0 mm2 at print z 8.2). Panel, cap, eyecup, knobs and gauge pass.
Failure. "Slicer review not run" hides failures that r7's own computed gate would catch now; the 292-pass headline is not comparable with r7's release audit.
Fix. Port `check_print_overhang` and the thin-wall/critical-feature checks into `run_shadow_checks.py` for every production part; declare any accepted support zones (r7 `PRINT_SUPPORT_ZONES` style) and fail on stale or undeclared ones.

### PRI-2 (blocker, latent) Plenum roof is not post-supported
Evidence. `roof.json`: the first roof layer over each bay is one unsupported region (cold 7600 mm2, hot 5099 mm2). Two-ended raster runs (anchored on post tops, frame or divider at both ends): cold bay best direction 67.5/112.5 deg max 43.8 mm (436-459 lines over 30 mm); hot bay best 157.5 deg max 47.1 mm (263 lines over 30 mm); along the axes 92.9 mm (x) and 97.4 mm (z). A 1.6 mm post on an 8 mm pitch meets only about 20 % of axis-parallel lines; the rest span the bay. The plenum report's `diagonal_between_post_surface_extent_mm 9.71` and "nominal 8 mm grid" are not spans (`shadow-plenum-checks.json` row `print_and_thermal_limits`). r7 `FDM.MAX_BRIDGE` = 30 mm (`layout.py:48`).
Failure. First roof layers sag or fail inside closed bays; strands and debris stay in the plenum and reduce the already small hot section (299.4 mm2). With supports enabled, the slicer fills the bays with supports that cannot be removed (the candidate itself bans that).
Fix. Replace the post grid with continuous ribs. Run them along the flow (x) so ribs also guide air to the mouths; at 10 mm pitch the bridge is under 9 mm, two-ended. Keep the underside mouths as rib-free lanes, or use a 45 deg self-supporting roof profile. Then re-run print_overhang (PRI-1) and the plenum section checks. Physical coupon still required after the CAD fix.

### PRI-3 (major, existing but understated) All four mouths have the front-mouth defect
Evidence. `vent_geometry.py:16-20`: the rear mouth removes the rear frame over Z5..75 (70 mm), the cold underside mouth over X-154..-83 (71 mm), the hot underside mouth over X-59..-5 (54 mm), the front mouth over Z5..40 (35 mm). r7-rule result (`overhang_b30.json`, print bboxes mapped): 665.9 mm2 unsupported at x -158..-85.1, z 0..73 (rear + cold underside) and 417.9 mm2 at x -56.8..0, z 0..38.4 (front + hot underside). Nearest posts are 7.2 mm (rear, underside) and 10.7 mm (front) from the open edge, so these are cantilevers well past r7's 1 mm. README/REVIEW/CHECKPOINT-STATUS name only the front mouth and "about 35 mm".
Failure. The rear mouth needs twice the documented span; both underside mouths carry the floor wall edge over air. The expanded coupon (X-110..0) omits the rear mouth and most of the cold underside mouth.
Fix. Give every mouth a 45 deg lintel: chamfer the roof edge down to the skin over 6 mm, or shape each mouth as a 45 deg/teardrop section. Update the hold text to list all four mouths.

### PRI-4 (major, latent) Carrier print pose floats the frame
Evidence. `manifest.json` print pose carrier `face_down +Y`. `model.py:176-194` frame y 17.2..20.2 and bosses y 16.2..20.2 (after the +3.2 shift); `structure_geometry.py:22-44` adds only the diagonal arm and root pads at y 17.2..22.2. In +Y-down pose only the arm touches the bed; the frame starts at print z 2.0 over air: 1963.1 mm2 unsupported, 27.4 mm bridges with hole edges (`overhang_b30.json`). The other face is not flat either (bosses stand 1 mm proud on -Y).
Failure. As posed, the load-bearing carrier needs a large support field under its frame; this is not declared and was never checked.
Fix. Thicken the frame on +Y to y 22.2 so the bed face is continuous (space exists up to the panel at y 22.2), or declare and check a support zone. Re-run the carrier screen with the real section.

### PRI-5 (minor, latent) Grip power-passage pocket roof
Evidence. base_grip (`face_down +Z`) unsupported 102.9 mm2 at model z -5.4, x -76.1..-66.1, y -11.5..8.2; bridge region 25.7 mm at x -83..-65 (`overhang_b30.json`). r7 base_grip: pass, longest 24.7 mm, 0 unsupported. The region is the new swept power passage / local 3 mm corner relief next to the J4 rear tongue (`power_geometry.py`; REVIEW "203.5 of 208 mm2").
Failure. Support scars or sag in a J4 mating pocket change the fit of a load-bearing joint.
Fix. Declare the support zone and keep it off J4 mating faces, or add a 45 deg roof to the passage.

### PRI-6 (minor, latent) Collar LR foot overhang
Evidence. `model.py:202` sets `body_r` 25 (r7 30). LR foot (y -19, z 44, d 7.6; r7 `layout.py` COLLAR feet) reaches 28.6 mm from the lens axis, 3.6 mm outside the body, with no ear. r7-rule: 11.0 mm2 unsupported at x 0.4, y -22.8..-18.1, z 40.2..45.4. r7 collar: pass, 0 unsupported.
Failure. Drooped first layers at the root of the compression foot that carries the J7-R load path.
Fix. Add an ear (as for TL/TR/LL) or a 45 deg fillet under LR.

### PRI-7 (major, latent) Revised collar not re-checked
Evidence. `model.py:197-209` `collar_setup()`: body_r 30 -> 25, LL foot (28, 36) -> (18, 30), lug y_out -35 -> -30, screw_y -31 -> -26.3, bit_relief_y -27 -> -22.8. No candidate file contains lens_clamp, lens_support, j7_float, inserts or M_sep (grep). My recomputation with r7's `check_lens_clamp` statics and r7's Kowa loads (axial 13.26 N, bending 0.363 N m, prying factor 2): anchor polygon margin 16.01 -> 14.43 mm (rule 10, pass); bolted-only triangle margin -8.80 -> -3.26 mm; max anchor reaction 59.3 -> 50.7 N. So the anchor statics improve. Two local margins shrink: the s_c4 washer (d 7.0, r7 `layout.py` COLLAR lug comment) now ends exactly at the bit-relief face (-26.3 + 3.5 = -22.8; r7 had 0.5 mm), leaving 0.25 mm for the d 6.5 bit; the lug wall outside the d 4.0 insert bore is 3.7 - 2.0 = 1.7 mm (r7 2.0; rule 1.6 loaded). Camera-to-tub/panel/carrier is checked only as overlap 0.0 (`verification.json` rows gs_camera/tub, /panel, /carrier); r7 `j7_float` enforced 0.4 mm axial / 0.5 mm lateral minimum gaps over 41 rows.
Failure. J7-R float and the collar clamp are user rules; zero overlap allows zero gap. The washer can bind on the relief wall at the step where s_c4 is driven straight.
Fix. Run r7 `check_lens_clamp`, `check_lens_support`, `check_inserts` and `j7_float` (min-gap) on the candidate collar/tub/panel; restore at least 0.5 mm washer-to-relief clearance. M1 stays open.

### PRI-8 (major, latent) Structural base is unreproducible; higher J4 model unreported
Evidence. `update_concealed_vent_structure.py:14-29` scales everything from `reference-export18-structural-binding.json` (J4 lip/head 8.51/9.41 MPa, carrier 3.39 MPa, grip 1.52/1.62 MPa, 0.90 N m). No generator for that JSON is in the repo (grep for `integrated_upper_body_screen` finds only the JSON, the scaler and the PDF builder). The same JSON holds `inherited_lip_at_integrated_load_MPa` 19.15 and `inherited_head_at_integrated_load_MPa` 16.72. Scaled by the 4.82 % moment rise, that model gives 20.07 / 17.53 MPa; with the 1.4 station-sharing factor, 28.1 MPa. The supplement reports only 8.92 / 9.86 MPa and does not explain the 2.25x difference.
Failure. The J4 coupon target and every stress figure rest on numbers nobody can regenerate, and the more severe J4 model is silently dropped.
Fix. Commit the free-body/section generator that produced the reference JSON; report both J4 models or state why the inherited model no longer applies; bind the generator hash in the supplement.

### PRI-9 (major, latent) 0.95 N m does not cover the fallback variant
Evidence. Same transfer applied to `out/original-kowa_lm6hc/manifest.json` (906.4 g, CoM z 30.55): upper mass 715.4 g, 5 g floor moment 1893.8 N mm, equal-share screen 0.976 N m, 70 % case 1.367 N m, grip 4.84 N m. Compact Fujinon: 0.764 N m. The script refuses non-tub/panel row changes (`update_concealed_vent_structure.py:20`), so no supplement exists for the documented fallback. All changed fallback rows (EVF, eyepiece, panel, sleeve, tub, stick) are upper-body parts, so the transfer is a fair estimate.
Fix. Compute each variant, or set the screen to at least 1.00 N m and the 70 % case to 1.37 N m.

### PRI-10 (major, latent) CSI slot is probably a main intake, not a small bypass
Evidence. CSI sleeve `model.py:263` box X-89..-77, Y-35.6..-25.4, Z41..68 (323.1 mm2), straight from the outer skin into the cavity. Blower inlet (cooler proxy `cots.py:108-117`, `layout.py:856-858`, mapped by the vertical transform) is at about X-99..-69, Z15..43, face at y -14.1. Orifice estimate: concealed cold path = mouths 846 mm2 in series with wall ports 420 mm2, effective about 376 mm2 before channel, post and turn losses; CSI path = one 323 mm2 orifice through a 10 mm sleeve, 0-25 mm from the blower inlet. Its conductance is at least 0.86x the whole concealed path.
Failure. A large share of intake air (likely half or more) enters through the visible broad-face slot, unfiltered, straight onto the fan. The concealment and dust arguments depend on the plenum path.
Fix. Add a printed CSI plug or cap fitted after CSI service (printed parts and plugged access holes are allowed), then re-evaluate the flow split. Keep the slot straight for the tool.

### PRI-11 (minor, latent) Hot plume over the collar clamp lug
Evidence. Front hot mouth `vent_geometry.py:20` X-2.6..0.1, Y-34..-28, Z5..40, facing +X. Collar lug `model.py:204` y_out -30, r7 lower_z 50..59 / upper_z 61..66, x 1..8.6, carrying the s_c4 pinch screw. The lug is 10 mm above the mouth top and overlaps it over y -30..-28.
Failure. In upright use warm exhaust rises past the clamp lug. Higher collar temperature speeds ASA creep and preload loss (M1, G-COL-1). Not in G-V-THERMAL or M1.
Fix. Add collar-lug temperature and preload retention to the powered thermal test; consider lowering or turning the front mouth.

### PRI-12 (minor, existing but understated) Occlusion is the normal case
Evidence. r7 `SPEC.md:437` puts the hand strap on the right side; with X forward and Z up, right is -Y, the plenum side. Candidate strap envelope X-103.2..-65.8, Y-21.7..4.7, Z-104.7..-0.2 (manifest row `strap`). The underside mouths (Y-34..-28 at Z0; X-154..-83 and X-59..-5) face down onto the gripping hand and carry 750 of the 1380 mm2 edge-mouth area (54 %).
Failure. Treating hand/strap occlusion as one of several cases understates it; unoccluded is the unusual case.
Fix. Make hand-plus-strap the baseline thermal case; consider moving intake area to the rear mouth and exhaust to the front.

### PRI-13 (minor, existing, quantified) Cleanout and inspection reach
Evidence. From `vent_geometry.py` bays: cold bay X-155.5..-65, Z2.5..97.5; its farthest point (-65, 97.5) is 93 mm from the rear mouth and 97 mm from the underside mouth. Hot bay farthest point (-62, 97.5) is 83 mm from the front mouth. Access is a 6 mm gap with 188 posts (`shadow-plenum-checks.json`). Wall ports sit at Z16..40, so the upper half of each bay carries little designed flow but holds the most remote spans. Both coupons have open cut edges.
Failure. Stringing between posts, sag or support debris cannot be seen or removed; no coupon shows this.
Fix. With ribs (PRI-2) make straight lanes from each mouth; or limit the gap to the flow band and back the upper skin solid; add a borescope check to G-V-PRINT.

### PRI-14 (minor, latent) No bed chamfer on the skin
Evidence. `vent_geometry.py:39` the skin is a sharp box on the bed face; r7 `layout.py:49` `BED_CHAMFER=0.6`.
Failure. Elephant-foot flare on the visible face perimeter and at the panel seam.
Fix. Add the 0.6 mm 45 deg bed chamfer to the skin outline.

### PRI-15 (info) Pressure loss is computable now
Evidence. Parallel-plate laminar loss 12 mu L V / h^2 for h 6 mm, L 70 mm, V 1 m/s is about 0.4 Pa; entry, turn and exit losses at 1 m/s add a few Pa. The candidate lists plenum pressure loss only as a physical gate (REVIEW s6 G-V-THERMAL).
Fix. Add a small flow-network model (mouths, channel, posts, ports, CSI slot, fan-curve band) as a computation gate before powered tests.

### PRI-16 (info) Balance by lens
Evidence. Manifests: compact Kowa 864.1 g, CoM 0.63 mm ahead of grip axis x -47; compact Fujinon 750.7 g, 11.19 mm behind; original Kowa 906.4 g, 6.99 mm behind (r7 Kowa 896.2 g, 1.55 mm ahead). r7 enforces no balance rule.
Fix. State per-lens balance in REVIEW; no action unless the user wants a balance rule.

## CAD/computation versus physical test

- CAD/computation now: PRI-1, -2, -3, -4, -5, -6, -7, -9, -10 (plug), -14, -15. PRI-8 needs the generator committed.
- Physical only: bridge sag and post bonding on a coupon after the CAD fix; cleanout borescope; warm creep of the collar lug (PRI-11); hand/strap occlusion and closed-body temperatures (PRI-12); real cooler registration and fan point.

## Probe status

- Completed: `probe_overhang.py` (r7 rule, all 10 print-pose STLs, `overhang_b30.json`) and `probe_roof.py` (`roof.json`).
- Not run: `probe_map.py`, `probe_overhang.py` with bridge_max 200, and `probe_thin.py` (thin-feature screen and camera min gap). They waited behind other agents' CAD jobs on the global lock (export_candidate, run_shadow_checks, export_shadow_alternatives) past this review's time box. Region coordinates above were mapped by hand from the manifest print poses. The scripts are ready for the fix phase; PRI-7's j7_float gap and the thin-wall result remain open items for that run.
- The committed snapshot is unchanged (`git status` clean after the probes).
